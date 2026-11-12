"""Static guards for the portable PYNQ-ZU DPU Block Design script."""

from pathlib import Path
import unittest


FPGA_DIR = Path(__file__).resolve().parents[1]


class PynqZuDpuBdContractTests(unittest.TestCase):
    def test_selects_a_supported_zynqmp_ps_ip_version(self) -> None:
        script = (FPGA_DIR / "create_pynq_zu_dpu_bd.tcl").read_text(encoding="utf-8")
        self.assertIn("xilinx.com:ip:zynq_ultra_ps_e:3.5", script)
        self.assertIn("xilinx.com:ip:zynq_ultra_ps_e:3.4", script)
        self.assertIn("xilinx.com:ip:zynq_ultra_ps_e:3.3", script)
        self.assertIn("PYNQ_ZU_DPU_PS_IP_VLNV", script)
        self.assertIn("-vlnv $ps_ip_vlnv", script)

    def test_configures_the_tracked_pynq_zu_board_repository(self) -> None:
        script = (FPGA_DIR / "create_pynq_zu_dpu_bd.tcl").read_text(encoding="utf-8")
        self.assertIn("board_repos XilinxBoardStore-master boards", script)
        self.assertIn("set_param board.repoPaths", script)
        self.assertIn("tul.com.tw:pynqzu:part0:1.1", script)

    def test_keeps_usb_on_ps_and_dpu_memory_interfaces_on_hp_ports(self) -> None:
        script = (FPGA_DIR / "create_pynq_zu_dpu_bd.tcl").read_text(encoding="utf-8")
        self.assertIn("PS MIO", script)
        self.assertIn("DPU0_M_AXI_DATA0", script)
        self.assertIn("S_AXI_HP0_FPD", script)
        self.assertIn("DPU0_M_AXI_DATA1", script)
        self.assertIn("S_AXI_HP1_FPD", script)
        self.assertIn("get_bd_addr_spaces zynq_ultra_ps_e_0/Data", script)
        self.assertIn("PYNQ_ZU_DPU_CONTROL_ADDRESS", script)


if __name__ == "__main__":
    unittest.main()
