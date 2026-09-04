/**
 * FlagPro Dashboard - Central State Manager
 * Holds symbols data, active simulation state, custom presets, and notifies components.
 */
const AppStateManager = (function() {
    'use strict';

    const state = {
        currentSymbol: 'EURUSD',
        activeTab: 'equity',
        allSymbolsData: {},
        customPresets: [],
        simState: {
            mode: 'kings',
            enabledKings: new Set(),
            allowedHours: new Array(24).fill(true),
            minProfit: 0.0,
            consecLossTrigger: 0,
            consecLossSkipCount: 1,
            consecLossSkipDay: false,
            showDrawdown: true
        }
    };

    const listeners = {
        'symbolChange': [],
        'dataUpdate': [],
        'simStateChange': []
    };

    function subscribe(event, callback) {
        if (listeners[event]) listeners[event].push(callback);
    }

    function emit(event, data) {
        if (listeners[event]) {
            listeners[event].forEach(cb => {
                try { cb(data); } catch(err) { console.error('Error in event listener:', err); }
            });
        }
    }

    function registerSymbolData(symbolName, data) {
        state.allSymbolsData[symbolName] = data;
        if (!state.currentSymbol || state.currentSymbol === symbolName) {
            setSymbol(symbolName, false);
        }
        emit('dataUpdate', { symbol: symbolName, data: data });
    }

    function getSymbolData(symbolName) {
        const sym = symbolName || state.currentSymbol;
        return state.allSymbolsData[sym] || null;
    }

    function setSymbol(symbolName, triggerEvent = true) {
        if (!state.allSymbolsData[symbolName]) return;
        state.currentSymbol = symbolName;
        const sData = state.allSymbolsData[symbolName];

        // Reset simState for this symbol
        state.simState.mode = 'kings';
        state.simState.enabledKings = new Set((sData.kings_sim_list || []).map(k => k.kk));
        state.simState.allowedHours = new Array(24).fill(true);
        state.simState.minProfit = 0.0;
        state.simState.consecLossTrigger = 0;
        state.simState.consecLossSkipCount = 1;
        state.simState.consecLossSkipDay = false;

        // Update selector in DOM if present
        const sel = document.getElementById('symbolSelector');
        if (sel && sel.value !== symbolName) sel.value = symbolName;

        if (triggerEvent) {
            emit('symbolChange', { symbol: symbolName, data: sData });
            emit('dataUpdate', { symbol: symbolName, data: sData });
        }
    }

    function getSimState() {
        return state.simState;
    }

    function updateSimState(patch) {
        Object.assign(state.simState, patch);
        emit('simStateChange', state.simState);
    }

    function getAllSymbols() {
        return Object.keys(state.allSymbolsData);
    }

    return {
        state: state,
        subscribe: subscribe,
        emit: emit,
        registerSymbolData: registerSymbolData,
        getSymbolData: getSymbolData,
        setSymbol: setSymbol,
        getSimState: getSimState,
        updateSimState: updateSimState,
        getAllSymbols: getAllSymbols
    };
})();
