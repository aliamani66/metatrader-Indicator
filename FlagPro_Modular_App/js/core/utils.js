// FlagPro Strategy Dashboard - Core Utility Functions

            function calcWaitMinutes(bts, et) {
                if (!bts || !et || bts === 'None' || et === 'None') return null;
                try {
                    let p1 = bts.substring(0, 16).replace(/[.]/g, '-');
                    let p2 = et.substring(0, 16).replace(/[.]/g, '-');
                    let d1 = new Date(p1.replace(' ', 'T') + ':00Z');
                    let d2 = new Date(p2.replace(' ', 'T') + ':00Z');
                    let diffSec = (d2.getTime() - d1.getTime()) / 1000;
                    if (!isNaN(diffSec) && diffSec >= 0) return Math.round((diffSec / 60) * 10) / 10;
                } catch(e) {}
                return null;
            }

            function formatDurationPersian(minutes) {
                if (minutes === null || minutes === undefined || isNaN(minutes) || minutes <= 0) return '۰ دقیقه';
                if (minutes < 60) return Math.round(minutes) + ' دقیقه';
                if (minutes < 1440) return (minutes / 60).toFixed(1) + ' ساعت';
                return (minutes / 1440).toFixed(1) + ' روز';
            }

            function formatDurationShort(minutes) {
                if (minutes === null || minutes === undefined || isNaN(minutes) || minutes <= 0) return '0m';
                if (minutes < 60) return Math.round(minutes) + 'm';
                if (minutes < 1440) return (minutes / 60).toFixed(1) + 'h';
                return (minutes / 1440).toFixed(1) + 'd';
            }


function formatLatencyShort(minutes) {
    if (minutes === null || minutes === undefined || isNaN(minutes) || minutes <= 0) return "-";
    if (minutes < 60) return Math.round(minutes) + "m";
    if (minutes < 1440) return (minutes / 60.0).toFixed(1) + "h";
    return (minutes / 1440.0).toFixed(1) + "d";
}

function formatLatencyPersian(minutes) {
    if (minutes === null || minutes === undefined || isNaN(minutes) || minutes <= 0) return "-";
    if (minutes < 60) return Math.round(minutes) + " دقیقه";
    if (minutes < 1440) {
        let h = (minutes / 60.0).toFixed(1);
        return h + " ساعت (" + Math.round(minutes) + " دقیقه)";
    }
    let d = (minutes / 1440.0).toFixed(1);
    let remH = Math.round((minutes % 1440) / 60.0);
    return d + " روز (" + remH + " ساعت)";
}

function calcLatencyStatsFromTrades(tradesList) {
    let delays = [];
    (tradesList || []).forEach(t => {
        let wm = null;
        if (t.wait_m !== undefined && typeof t.wait_m === 'number' && t.wait_m > 0) {
            wm = t.wait_m;
        } else if (t.wm !== undefined && typeof t.wm === 'number' && t.wm > 0) {
            wm = t.wm;
        } else if (t.en_t && t.box_t) {
            try {
                let dt1 = new Date(t.box_t.replace(/\./g, '-'));
                let dt2 = new Date(t.en_t.replace(/\./g, '-'));
                let diffM = (dt2 - dt1) / (1000 * 60);
                if (diffM >= 0) wm = diffM;
            } catch(e) {}
        }
        if (wm !== null && !isNaN(wm) && wm >= 0) {
            delays.push(wm);
        }
    });

    if (delays.length === 0) {
        return {
            cnt: 0, min: 0, max: 0, avg: 0, med: 0, p90: 0,
            avg_fmt: '-', min_fmt: '-', max_fmt: '-', med_fmt: '-', p90_fmt: '-',
            avg_short: '-', min_short: '-', max_short: '-', med_short: '-', p90_short: '-'
        };
    }
    delays.sort((a, b) => a - b);
    let n = delays.length;
    let d_min = delays[0];
    let d_max = delays[n - 1];
    let d_avg = delays.reduce((a, b) => a + b, 0) / n;
    let d_med = delays[Math.floor(n / 2)];
    let d_p90 = delays[Math.floor(n * 0.90)];
    return {
        cnt: n,
        min: d_min, max: d_max, avg: d_avg, med: d_med, p90: d_p90,
        avg_fmt: formatLatencyPersian(d_avg),
        min_fmt: formatLatencyPersian(d_min),
        max_fmt: formatLatencyPersian(d_max),
        med_fmt: formatLatencyPersian(d_med),
        p90_fmt: formatLatencyPersian(d_p90),
        avg_short: formatLatencyShort(d_avg),
        min_short: formatLatencyShort(d_min),
        max_short: formatLatencyShort(d_max),
        med_short: formatLatencyShort(d_med),
        p90_short: formatLatencyShort(d_p90)
    };
}

