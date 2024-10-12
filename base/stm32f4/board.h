// ///////////////////////////////////////////////////////////// //
// Hardware abstraction layer for all different supported boards //
// ///////////////////////////////////////////////////////////// //
#include "brd/decs.h"
#include "brd/funcs.h"

// ///// Board definition and detection ///// //
#include "stm32f4/lladc.h"
#include "drvrs/harness.h"
#include "drvrs/fan.h"
#include "stm32f4/llfan.h"
#include "drvrs/clock.h"
#include "brd/board.h"

void detect_board_type(void) {
  // Set GPIO outputs (SPI lines floating detection not reliable, ESP/GPS needs to be enabled)
  set_gpio_output(GPIOC, 14, 1);
  set_gpio_output(GPIOC, 5, 1);

  // Detection logic simplified to only detect CARLINK type
  hw_type = HW_TYPE_CARLINK;
  current_board = &ex_board; // Kept as requested
}
