/*
 * DPUCZDX8G configuration for the PYNQ-ZU xczu5eg feasibility build.
 *
 * This is intentionally a one-core B512 starting point.  It is not a model
 * artifact: every architecture-affecting option below must match the
 * arch.json used later to compile an INT8 model into a deployable .xmodel.
 * The configuration remains provisional until Vivado implementation proves
 * resource/timing closure on the actual board target.
 */

`define B512
`define URAM_DISABLE
`define DRAM_DISABLE
`define RAM_USAGE_LOW
`define CHANNEL_AUGMENTATION_ENABLE
`define ALU_PARALLEL_DEFAULT
`define CONV_RELU_LEAKYRELU_RELU6
`define ALU_RELU_RELU6
`define DSP48_USAGE_HIGH
`define LOWPOWER_DISABLE
`define MPSOC
