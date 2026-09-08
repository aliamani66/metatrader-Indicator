/**
 * FlagPro Dashboard - Global Configuration & Constants
 */
const AppConfig = {
    appName: 'FlagPro Master Strategy Dashboard',
    version: '2.60',
    defaultSymbol: 'EURUSD',
    frictionPerTrade: 0.48, // 0.04 lot friction ($0.48)
    bridgeServerUrl: 'http://127.0.0.1:8288',
    storagePrefix: 'FLAGPRO_',
    supportedTimeframes: ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'],
    targetRatios: [1, 2, 3, 4],
    defaultBalance: 10000.0,
    tabsList: [
        { id: 'equity', title: 'رشد سرمایه و شبیه‌ساز', icon: '📈' },
        { id: 'kings', title: 'سلاطین برگزیده', icon: '👑' },
        { id: 'scaleout', title: 'کالبدشکافی پلکانی (TP1..4)', icon: '🎯' },
        { id: 'timeframes', title: 'عملکرد تایم‌فریم‌ها', icon: '⏱️' },
        { id: 'filters', title: 'فیلترهای استراتژیک', icon: '🔍' },
        { id: 'loss_intel', title: 'هوش ضرر و استاپ', icon: '🛡️' },
        { id: 'weekly', title: 'کارنامه هفته به هفته', icon: '📊' },
        { id: 'presets', title: 'پیشنهادات استراتژیک EA', icon: '🤖' },
        { id: 'tester_compare', title: 'کالبدشکافی تست MT5', icon: '🔬' },
        { id: 'optimizer', title: 'بهینه‌ساز شبکه هوشمند', icon: '⚡' },
        { id: 'journal', title: 'ژورنال جامع معاملات', icon: '📋' }
    ]
};

// Freeze to prevent accidental mutation
if (typeof Object.freeze === 'function') {
    Object.freeze(AppConfig);
}
