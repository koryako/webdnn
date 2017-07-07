from typing import List

from webdnn.backend.code_generator.allocator import MemoryLayout
from webdnn.backend.code_generator.injectors.buffer_injector import BufferInjector
from webdnn.backend.code_generator.injectors.kernel_name_injector import KernelNameInjector
from webdnn.backend.webassembly.generator import WebassemblyDescriptorGenerator
from webdnn.backend.webassembly.kernel import Kernel
from webdnn.graph.operators.reshape import Reshape
from webdnn.util.misc import mul

template = """
void %%FUNC_NAME%%(const int * %%META_BUFFER%% )
{
    const float *x = %%LOAD_BUFFER(reshape_x)%%;
    float *y = %%LOAD_BUFFER(reshape_y)%%;

    const int N = %%LOAD_BUFFER(reshape_N)%%;

    for (int gid = 0; gid < N; gid += 1) {
        y[gid] = x[gid];
    }
}
"""


@WebassemblyDescriptorGenerator.register_handler(Reshape)
def reshape(op: Reshape, memory_layout: MemoryLayout) -> List[Kernel]:
    # Operation without need for transposition is currently supported
    x = memory_layout[op.inputs["x"]]
    y = memory_layout[op.outputs["y"]]

    assert x.variable.order == op.parameters["in_order"]
    assert y.variable.order == op.parameters["out_order"]
    assert y.variable.size == mul(op.parameters["out_shape"])

    buffer_injector = BufferInjector()
    buffer_injector.register({
        "reshape_x": x,
        "reshape_y": y,
        "reshape_N": y.variable.size,
    })

    name_injector = KernelNameInjector(op)

    source = template
    source = buffer_injector.inject(source)
    source = name_injector.inject(source)

    kernel = Kernel(
        {name_injector.name: source},
        name_injector.name,
        buffer_injector.buffer,
        buffer_injector.unresolved_value_list
    )

    return [kernel]
