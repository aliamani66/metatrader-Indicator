/**
 * FlagPro Master Equity Simulation Tab Orchestrator (Modular Architecture)
 * 
 * Cohesive Submodules:
 *  - js/equity/equity_presets.js  : Global simulation state & custom preset management
 *  - js/equity/equity_controls.js : Interactive Kings grid, hours bar, and MT5 filter checkboxes
 *  - js/equity/equity_engine.js   : Sequential trade simulation, circuit breakers, and optimizer
 *  - js/equity/equity_canvas.js   : High-performance Canvas renderer, tooltip tracking, and layout controls
 */

function initSimUI() {
    if (typeof renderSimKingsGrid === 'function') renderSimKingsGrid();
    if (typeof renderSimHoursBar === 'function') renderSimHoursBar();
    if (typeof syncMT5FilterCheckboxesUI === 'function') syncMT5FilterCheckboxesUI();
    if (typeof loadCustomPresets === 'function') loadCustomPresets();
    if (typeof runEquitySimulation === 'function') runEquitySimulation();
}

window.initSimUI = initSimUI;
