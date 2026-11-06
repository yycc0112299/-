r"""Build the PYNQ-ZU USB-video A53 platform and control ELF with Vitis 2024.2.

Run with the Embedded Vitis CLI, for example:
  set PYNQ_ZU_USB_VIDEO_XSA=C:\short\pynq_zu_usb_video.xsa
  C:\Xilinx_Embedded_2024_2\Vitis\2024.2\bin\vitis.bat -s build_vitis_embedded.py

Set PYNQ_ZU_VITIS_WORKSPACE to a short, empty Windows path (default C:\pynq_vitis).
Long Windows paths make the A53 compiler fail while creating dependency files.
"""
import os
import vitis


def required_path(name):
    value = os.environ.get(name)
    if not value or not os.path.isfile(value):
        raise RuntimeError(f"{name} must name an existing XSA file")
    return value


xsa = required_path("PYNQ_ZU_USB_VIDEO_XSA")
workspace = os.environ.get("PYNQ_ZU_VITIS_WORKSPACE", r"C:\pynq_vitis")
if os.path.exists(workspace):
    raise RuntimeError(f"Workspace must be empty: {workspace}")

source_dir = os.path.join(os.path.dirname(__file__), "src")
client = vitis.create_client()
client.set_workspace(workspace)

platform = client.create_platform_component(
    name="pynq_zu_usb_video_platform",
    hw_design=xsa,
    cpu="psu_cortexa53_0",
    os="standalone",
    domain_name="standalone_domain",
)
platform.build()
client.add_platform_repos(workspace)
platform_xpfm = client.find_platform_in_repos("pynq_zu_usb_video_platform")
app = client.create_app_component(
    name="pynq_zu_usb_video_app",
    platform=platform_xpfm,
    domain="standalone_domain",
    template="hello_world",
)
app.import_files(
    from_loc=source_dir,
    files=["main.c", "video_control.c", "video_control.h"],
    dest_dir_in_cmp="src",
)
app_src = os.path.join(workspace, "pynq_zu_usb_video_app", "src")
os.unlink(os.path.join(app_src, "helloworld.c"))
config_path = os.path.join(app_src, "UserConfig.cmake")
with open(config_path, encoding="utf-8") as handle:
    config = handle.read()
with open(config_path, "w", encoding="utf-8", newline="") as handle:
    handle.write(config.replace('"helloworld.c"\n', ""))
app.build()
print(os.path.join(workspace, "pynq_zu_usb_video_app", "build", "pynq_zu_usb_video_app.elf"))
