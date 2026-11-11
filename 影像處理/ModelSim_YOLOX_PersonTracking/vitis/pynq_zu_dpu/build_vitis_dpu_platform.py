r"""Create the A53 standalone Vitis platform for the PYNQ-ZU B512 DPU XSA.

This is a hardware-handoff verification only.  It deliberately does not create
a DPU application: native DPU execution needs the matching Linux DPU driver,
VART runtime, CMA/device-tree configuration, and an INT8 .xmodel.

Run with the complete Vitis Embedded 2024.2 CLI, for example:
  set PYNQ_ZU_DPU_XSA=C:\short\pynq_zu_dpu_b512.xsa
  set PYNQ_ZU_DPU_VITIS_WORKSPACE=C:\pynq_dpu_vitis
  C:\Xilinx_Embedded_2024_2\Vitis\2024.2\bin\vitis.bat -s build_vitis_dpu_platform.py
"""

import os

import vitis


def required_file(name):
    value = os.environ.get(name)
    if not value or not os.path.isfile(value):
        raise RuntimeError(f"{name} must name an existing XSA file")
    return value


xsa = required_file("PYNQ_ZU_DPU_XSA")
workspace = os.environ.get("PYNQ_ZU_DPU_VITIS_WORKSPACE", r"C:\pynq_dpu_vitis")
if os.path.exists(workspace):
    raise RuntimeError(f"Workspace must be empty: {workspace}")

client = vitis.create_client()
client.set_workspace(workspace)
platform = client.create_platform_component(
    name="pynq_zu_dpu_platform",
    hw_design=xsa,
    cpu="psu_cortexa53_0",
    os="standalone",
    domain_name="standalone_domain",
)
platform.build()
client.add_platform_repos(workspace)
platform_xpfm = client.find_platform_in_repos("pynq_zu_dpu_platform")
if not platform_xpfm or not os.path.isfile(platform_xpfm):
    raise RuntimeError("Vitis did not export the PYNQ-ZU DPU platform XPFM")
print(f"PYNQ_ZU_DPU_VITIS_PLATFORM_PASS={platform_xpfm}")
