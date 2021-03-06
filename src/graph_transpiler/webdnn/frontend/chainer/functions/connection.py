import chainer

from webdnn.frontend.chainer.converter import ChainerConverter
from webdnn.frontend.constraints import unify_order
from webdnn.frontend.util import check_broadcast_constraints
from webdnn.graph.axis import Axis
from webdnn.graph.operators.convolution2d import Convolution2D
from webdnn.graph.operators.deconvolution2d import Deconvolution2D
from webdnn.graph.operators.linear import Linear
from webdnn.graph.operators.reinterpret_axis import ReinterpretAxis
from webdnn.graph.operators.reshape import Reshape
from webdnn.graph.operators.transpose import Transpose
from webdnn.graph.order import OrderNC, OrderNCHW, OrderCNHW, Order, OrderCN, OrderC
from webdnn.graph.variables.constant_variable import ConstantVariable
from webdnn.util.misc import mul


@ChainerConverter.register_handler("BilinearFunction")
def _convert_bilinear_function(converter: ChainerConverter, c_op: "chainer.functions.connection.bilinear.BilinearFunction"):
    # TODO
    raise NotImplementedError("[ChainerConverter] BilinearFunction is not supported")


@ChainerConverter.register_handler("Convolution2DFunction")
def _convert_convolution_2d(converter: ChainerConverter, c_op: "chainer.functions.connection.convolution_2d.Convolution2DFunction"):
    x = converter.get_variable(c_op.inputs[0])
    w = converter.get_variable(c_op.inputs[1])

    unify_order(x.order, OrderNCHW)
    unify_order(w.order, OrderNCHW)

    conv_opr = Convolution2D(None,
                             ksize=(w.shape_dict[Axis.H], w.shape_dict[Axis.W]),
                             stride=(c_op.sy, c_op.sx),
                             padding=(c_op.ph, c_op.pw))

    y, = conv_opr(x, w)

    if len(c_op.inputs) == 3:
        # with bias
        b = converter.get_variable(c_op.inputs[2])
        unify_order(b.order, OrderC)
        y = y + b

    converter.set_variable(c_op.outputs[0](), y)


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("ConvolutionND")
def _convert_convolution_nd(converter: ChainerConverter, c_op: "chainer.functions.connection.convolution_nd.ConvolutionND"):
    # TODO
    raise NotImplementedError("[ChainerConverter] ConvolutionND is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("Deconvolution2DFunction")
def _convert_deconvolution_2d(converter: ChainerConverter, c_op: "chainer.functions.connection.deconvolution_2d.Deconvolution2DFunction"):
    x = converter.get_variable(c_op.inputs[0])
    w = converter.get_variable(c_op.inputs[1])

    unify_order(x.order, OrderNCHW)
    unify_order(w.order, OrderCNHW)

    deconv_opr = Deconvolution2D(None,
                                 ksize=(w.shape_dict[Axis.H], w.shape_dict[Axis.W]),
                                 stride=(c_op.sy, c_op.sx),
                                 padding=(c_op.ph, c_op.pw))

    y, = deconv_opr(x, w)

    if len(c_op.inputs) == 3:
        # with bias
        b = converter.get_variable(c_op.inputs[2])
        unify_order(b.order, OrderC)
        y = y + b

    converter.set_variable(c_op.outputs[0](), y)


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("DeconvolutionND")
def _convert_deconvolution_nd(converter: ChainerConverter, c_op: "chainer.functions.connection.deconvolution_nd.DeconvolutionND"):
    # TODO
    raise NotImplementedError("[ChainerConverter] DeconvolutionND is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("DepthwiseConvolution2D")
def _convert_depthwise_convolution_2d(converter: ChainerConverter,
                                      c_op: "chainer.functions.connection.depthwise_convolution_2d.DepthwiseConvolution2D"):
    # TODO
    raise NotImplementedError("[ChainerConverter] DepthwiseConvolution2D is not supported")


@ChainerConverter.register_handler("DilatedConvolution2DFunction")
def _convert_selected_item(converter: ChainerConverter,
                           c_op: "chainer.functions.connection.dilated_convolution_2d.DilatedConvolution2DFunction"):
    x = converter.get_variable(c_op.inputs[0])
    w = converter.get_variable(c_op.inputs[1])

    unify_order(x.order, OrderNCHW)
    unify_order(w.order, OrderNCHW)

    # when dx == 1, it means ordinary convolution.
    conv_opr = Convolution2D(None,
                             ksize=(w.shape_dict[Axis.H], w.shape_dict[Axis.W]),
                             stride=(c_op.sy, c_op.sx),
                             padding=(c_op.ph, c_op.pw),
                             dilation_rate=(c_op.dx, c_op.dy))

    y, = conv_opr(x, w)

    if len(c_op.inputs) == 3:
        # with bias
        bias = converter.get_variable(c_op.inputs[2])
        unify_order(bias.order, OrderC)
        y = y + bias

    converter.set_variable(c_op.outputs[0](), y)


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("EmbedIDFunction")
def _convert_embed_id(converter: ChainerConverter, c_op: "chainer.functions.connection.embed_id.EmbedIDFunction"):
    # TODO
    raise NotImplementedError("[ChainerConverter] EmbedIDFunction is not supported")


@ChainerConverter.register_handler("LinearFunction")
def _convert_linear_function(converter: ChainerConverter, c_op: "chainer.functions.connection.linear.LinearFunction"):
    x = converter.get_variable(c_op.inputs[0])
    w = converter.get_variable(c_op.inputs[1])  # type: ConstantVariable

    x2, = Reshape(None, in_order=x.order, out_order=OrderNC, out_shape=[x.shape[0], mul(x.shape[1:])])(x)
    w2, = ReinterpretAxis(None, in_order=w.order, out_order=OrderNC)(w)
    w2, = Transpose(None)(w2)
    w2.change_order(OrderCN)

    y, = Linear(None)(x2, w2)
    y, = ReinterpretAxis(None, in_order=y.order, out_order=Order([x.order.axes[0], w.order.axes[0]]))(y)

    if len(c_op.inputs) == 3:
        # with bias
        b = converter.get_variable(c_op.inputs[2])
        check_broadcast_constraints(y, b)
        y = y + b

    converter.set_variable(c_op.outputs[0](), y)


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("NStepBiGRU")
def _convert_n_step_bigru(converter: ChainerConverter, c_op: "chainer.functions.NStepBiGRU"):
    # TODO
    raise NotImplementedError("[ChainerConverter] NStepBiGRU is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("NStepGRU")
def _convert_n_step_gru(converter: ChainerConverter, c_op: "chainer.functions.NStepGRU"):
    # TODO
    raise NotImplementedError("[ChainerConverter] NStepGRU is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("NStepBiLSTM")
def _convert_n_step_bilstm(converter: ChainerConverter, c_op: "chainer.functions.NStepBiLSTM"):
    # TODO
    raise NotImplementedError("[ChainerConverter] NStepBiLSTM is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("NStepLSTM")
def _convert_n_step_lstm(converter: ChainerConverter, c_op: "chainer.functions.NStepLSTM"):
    # TODO
    raise NotImplementedError("[ChainerConverter] NStepLSTM is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("NStepBiRNNReLU")
def _convert_n_step_birnn_relu(converter: ChainerConverter, c_op: "chainer.functions.NStepBiRNNReLU"):
    # TODO
    raise NotImplementedError("[ChainerConverter] NStepBiRNNReLU is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("NStepBiRNNTanh")
def _convert_n_step_birnn_tanh(converter: ChainerConverter, c_op: "chainer.functions.NStepBiRNNTanh"):
    # TODO
    raise NotImplementedError("[ChainerConverter] NStepBiRNNTanh is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("NStepRNNReLU")
def _convert_n_step_rnn_relu(converter: ChainerConverter, c_op: "chainer.functions.NStepRNNReLU"):
    # TODO
    raise NotImplementedError("[ChainerConverter] NStepRNNReLU is not supported")


# noinspection PyUnusedLocal
@ChainerConverter.register_handler("NStepRNNTanh")
def _convert_n_step_rnn_tanh(converter: ChainerConverter, c_op: "chainer.functions.NStepRNNTanh"):
    # TODO
    raise NotImplementedError("[ChainerConverter] NStepRNNTanh is not supported")
