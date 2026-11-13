"""Behavioral contract for staging the official DPU 4.0 PetaLinux additions."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "prepare_dpu_4_0_petalinux_project.py"


def load_module():
    spec = importlib.util.spec_from_file_location("prepare_dpu_4_0_petalinux_project", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PrepareDpu40PetaLinuxProjectTests(unittest.TestCase):
    def create_official_reference(self, root: Path) -> Path:
        meta_user = root / "project-spec" / "meta-user"
        kernel = meta_user / "recipes-kernel" / "linux"
        kernel.mkdir(parents=True)
        (kernel / "linux-xlnx_%.bbappend").write_text(
            'SRC_URI += "file://0001-add_dpu_compatibale-with-dpuczdx8g-4.0.patch"\n',
            encoding="utf-8",
        )
        kernel_files = kernel / "linux-xlnx"
        kernel_files.mkdir()
        (kernel_files / "bsp.cfg").write_text("CONFIG_XILINX_DPU=y\n", encoding="utf-8")
        (kernel_files / "0001-add_dpu_compatibale-with-dpuczdx8g-4.0.patch").write_text(
            '+\t{ .compatible = "xlnx,dpuczdx8g-4.0" },\n', encoding="utf-8"
        )
        for package in ("vart", "xir", "unilog", "target-factory", "vitis-ai-library"):
            recipe = meta_user / "recipes-vitis-ai" / package
            recipe.mkdir(parents=True)
            (recipe / f"{package}_2.5.bb").write_text(
                f"SUMMARY = \"{package}\"\n", encoding="utf-8"
            )
        return meta_user

    def test_stages_driver_and_runtime_recipes_without_losing_existing_rootfs_entries(self) -> None:
        """Removing the DPU patch/recipes or replacing user settings must fail this contract."""
        module = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            official = self.create_official_reference(root / "official")
            project = root / "project"
            rootfs = project / "project-spec" / "meta-user" / "conf" / "user-rootfsconfig"
            rootfs.parent.mkdir(parents=True)
            rootfs.write_text("CONFIG_existing_package\nCONFIG_vart=y\n", encoding="utf-8")

            manifest = module.stage_reference(project, official)

            target_meta_user = project / "project-spec" / "meta-user"
            self.assertTrue(
                (target_meta_user / "recipes-kernel" / "linux" /
                 "linux-xlnx" / "0001-add_dpu_compatibale-with-dpuczdx8g-4.0.patch").is_file()
            )
            self.assertTrue(
                (target_meta_user / "recipes-vitis-ai" / "vart" / "vart_2.5.bb").is_file()
            )
            self.assertTrue(
                (target_meta_user / "recipes-vitis-ai" / "xir" / "xir_2.5.bb").is_file()
            )
            graph_runner_append = (
                target_meta_user / "recipes-vitis-ai" / "vitis-ai-library" /
                "vitis-ai-library_2.5.bbappend"
            )
            self.assertEqual(
                graph_runner_append.read_text(encoding="utf-8"),
                'PACKAGECONFIG:append = " python"\n',
            )
            rootfs_text = rootfs.read_text(encoding="utf-8")
            self.assertIn("CONFIG_existing_package", rootfs_text)
            self.assertIn("CONFIG_vart", rootfs_text)
            self.assertIn("CONFIG_xir", rootfs_text)
            self.assertNotIn("CONFIG_vart=y", rootfs_text)
            image_append = (
                target_meta_user / "recipes-core" / "images" /
                "petalinux-image-minimal.bbappend"
            )
            self.assertTrue(image_append.is_file())
            self.assertEqual(
                image_append.read_text(encoding="utf-8"),
                'IMAGE_INSTALL:append = " vart xir unilog target-factory vitis-ai-library"\n',
            )
            self.assertEqual(manifest["dpu_ip_version"], "4.0")

    def test_rejects_reference_without_exact_dpu_driver_contract(self) -> None:
        """Copying arbitrary PetaLinux recipes must not masquerade as DPU 4.0 integration."""
        module = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            (project / "project-spec" / "meta-user" / "conf").mkdir(parents=True)
            incomplete = root / "incomplete" / "project-spec" / "meta-user"
            (incomplete / "recipes-vitis-ai").mkdir(parents=True)

            with self.assertRaisesRegex(ValueError, "DPU 4.0"):
                module.stage_reference(project, incomplete)

    def test_reads_quoted_petalinux_2022_1_version_from_settings(self) -> None:
        """A release mismatch must not be hidden by a quoted settings value."""
        module = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            settings = Path(temporary) / "settings.sh"
            settings.write_text('export PETALINUX_VER="2022.1"\n', encoding="utf-8")
            self.assertEqual(module.petalinux_version(settings), "2022.1")


if __name__ == "__main__":
    unittest.main()
