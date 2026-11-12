// Cross-compile-only ABI smoke test for the matching VART/XIR target SDK.
// It deliberately does not run without a real DPU subgraph and .xmodel.

#include <vart/runner.hpp>

int main() {
  const auto runner = vart::Runner::create_runner(
      static_cast<const xir::Subgraph*>(nullptr), "run");
  return runner == nullptr ? 0 : 0;
}
