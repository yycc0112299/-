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
    def test_runtime_recipe_maps_the_board_acceptance_gate_into_person_tracking(self) -> None:
        module = load_module()
        source = Path("vitis") / "pynq_zu_dpu" / "linux" / "verify_dpu_runtime.py"
        target = Path("person_tracking") / "verify_dpu_runtime.py"
        self.assertIn((source, target), module.PROJECT_RUNTIME_SOURCE_MAPPINGS)

    def test_runtime_recipe_stages_cross_camera_fusion_dependencies(self) -> None:
        module = load_module()
        expected = {
            Path("person_tracking") / "appearance_features.py",
            Path("person_tracking") / "cross_camera.py",
            Path("person_tracking") / "peer_protocol.py",
            Path("person_tracking") / "pynq_cross_camera_fusion.py",
            Path("person_tracking") / "pynq_yolov8_peer.py",
            Path("person_tracking") / "pynq_wifi_peer_preflight.py",
        }
        self.assertTrue(expected.issubset(set(module.PROJECT_RUNTIME_SOURCE_FILES)))

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
            kernel_config = (
                target_meta_user / "recipes-kernel" / "linux" / "linux-xlnx" /
                "bsp.cfg"
            ).read_text(encoding="utf-8")
            for option in (
                "CONFIG_USB_SUPPORT=y",
                "CONFIG_USB_DWC3=y",
                "CONFIG_USB_DWC3_DUAL_ROLE=y",
                "CONFIG_MEDIA_SUPPORT=y",
                "CONFIG_MEDIA_USB_SUPPORT=y",
                "CONFIG_USB_VIDEO_CLASS=y",
            ):
                self.assertIn(option, kernel_config)
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
                'IMAGE_INSTALL:append = " vart xir unilog target-factory vitis-ai-library python3-modules python3-numpy python3-opencv"\n',
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

    def test_stages_a_nonempty_compiled_xmodel_as_a_rootfs_package(self) -> None:
        """The deployment image must receive the exact compiled model, not its host path."""
        module = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            official = self.create_official_reference(root / "official")
            project = root / "project"
            (project / "project-spec" / "meta-user" / "conf").mkdir(parents=True)
            xmodel = root / "yolov8n_b512.xmodel"
            xmodel.write_bytes(b"compiled-dpu-model")

            manifest = module.stage_reference(project, official, xmodel=xmodel)

            model_dir = (project / "project-spec" / "meta-user" / "recipes-apps" /
                         "pynq-yolov8-model")
            self.assertEqual(
                (model_dir / "files" / "yolov8n_b512.xmodel").read_bytes(),
                b"compiled-dpu-model",
            )
            recipe = (model_dir / "pynq-yolov8-model.bb").read_text(encoding="utf-8")
            self.assertIn('SRC_URI = "file://yolov8n_b512.xmodel"', recipe)
            self.assertIn("/opt/models/yolov8n_b512.xmodel", recipe)
            image_append = (project / "project-spec" / "meta-user" / "recipes-core" /
                            "images" / "petalinux-image-minimal.bbappend")
            self.assertIn("pynq-yolov8-model", image_append.read_text(encoding="utf-8"))
            self.assertEqual(manifest["xmodel"]["sha256"], module.hash_file(xmodel))

    def test_restage_accepts_a_model_already_at_its_recipe_destination(self) -> None:
        """Incremental image builds must not fail merely because the model is staged."""
        module = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            official = self.create_official_reference(root / "official")
            project = root / "project"
            (project / "project-spec" / "meta-user" / "conf").mkdir(parents=True)
            source = root / "yolov8n_b512.xmodel"
            source.write_bytes(b"compiled-dpu-model")
            module.stage_reference(project, official, xmodel=source)
            staged = (project / "project-spec" / "meta-user" / "recipes-apps" /
                      "pynq-yolov8-model" / "files" / "yolov8n_b512.xmodel")

            manifest = module.stage_reference(project, official, xmodel=staged)

            self.assertEqual(manifest["xmodel"]["sha256"], module.hash_file(staged))

    def test_rejects_an_empty_or_wrong_extension_xmodel(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            official = self.create_official_reference(root / "official")
            project = root / "project"
            (project / "project-spec" / "meta-user" / "conf").mkdir(parents=True)
            empty_model = root / "empty.xmodel"
            empty_model.touch()
            with self.assertRaisesRegex(ValueError, "nonempty .xmodel"):
                module.stage_reference(project, official, xmodel=empty_model)

    def test_stages_the_minimal_graph_runner_and_tracker_sources_for_the_rootfs(self) -> None:
        """A booted SD image must not require an SSH copy before first DPU tracking."""
        module = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            official = self.create_official_reference(root / "official")
            project = root / "project"
            (project / "project-spec" / "meta-user" / "conf").mkdir(parents=True)
            runtime = root / "runtime"
            for source_relative, target_relative in module.PROJECT_RUNTIME_SOURCE_MAPPINGS:
                source = runtime / source_relative
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text(f"# {source_relative.as_posix()}\n", encoding="utf-8")

            manifest = module.stage_reference(project, official, runtime_source=runtime)

            package_dir = (project / "project-spec" / "meta-user" / "recipes-apps" /
                           "pynq-yolov8-runtime")
            for source_relative, target_relative in module.PROJECT_RUNTIME_SOURCE_MAPPINGS:
                self.assertEqual((package_dir / "files" / target_relative).read_text(encoding="utf-8"),
                                 f"# {source_relative.as_posix()}\n")
            recipe = (package_dir / "pynq-yolov8-runtime.bb").read_text(encoding="utf-8")
            self.assertIn('LICENSE = "CLOSED"', recipe)
            self.assertIn("/opt/pynq-yolov8/person_tracking/pynq_yolov8_dpu_inference.py", recipe)
            image_append = (project / "project-spec" / "meta-user" / "recipes-core" /
                            "images" / "petalinux-image-minimal.bbappend")
            self.assertIn("pynq-yolov8-runtime", image_append.read_text(encoding="utf-8"))
            self.assertEqual(manifest["runtime"]["target_root"], "/opt/pynq-yolov8")

    def test_rejects_an_incomplete_runtime_source_tree(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            official = self.create_official_reference(root / "official")
            project = root / "project"
            (project / "project-spec" / "meta-user" / "conf").mkdir(parents=True)
            runtime = root / "runtime"
            runtime.mkdir()
            with self.assertRaisesRegex(ValueError, "runtime source is missing"):
                module.stage_reference(project, official, runtime_source=runtime)


if __name__ == "__main__":
    unittest.main()
