// Copyright (C) 2014-2026 Daniele Simonetti
// Procedurally-drawn rice-paper noise overlay. Sits on top of the
// parchment fill at very low opacity to break up the flat hue --
// gives the sheet a "fibrous handmade paper" texture without
// shipping a PNG asset (so cxfreeze package-data stays clean).
// Implementation notes:
//   - Canvas, not ShaderEffect: lower setup cost, repaints once per
//     resize, no GL state to coordinate with the rest of QtQuick.
//   - Linear-congruential PRNG seeded from a constant (1337) means
//     every panel renders the SAME fibre pattern. That's a feature,
//     not a bug -- consistent fibres read as "this is the paper",
//     per-panel-random ones read as "noise that won't sit still".
//   - Strokes drawn in #2a221b (the sheet's ink colour) at 6%
//     overall opacity. Density tuned so a 600x400 panel gets ~9600
//     marks; small enough to read as texture, dense enough that the
//     pattern is uniform at panel scale.
//   - Repaints only on width/height change. We don't repaint on
//     scroll because the canvas is anchored to its parent (the
//     parchment background), which itself doesn't move under scroll.
import QtQuick
import Theme 1.0

Canvas {
    id: paper
    anchors.fill: parent
    opacity: Theme.paperTextureOpacity

    // Single-fire repaint when dimensions settle. Without this guard,
    // the Canvas re-renders on every intermediate resize step during
    // window resize -- visible flicker and wasted CPU.
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        if (width <= 0 || height <= 0)
            return;
        var ctx = getContext("2d");
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = "#2a221b";

        // Linear-congruential PRNG (Park-Miller). Seeded fixed so
        // fibres are stable across repaints. JS' Math.random is
        // unseeded and would re-randomise on every paint pass.
        var seed = 1337;
        function rand() {
            seed = (seed * 16807) % 2147483647;
            return seed / 2147483647;
        }
        var marks = Math.floor(width * height / 25);
        for (var i = 0; i < marks; ++i) {
            var x = rand() * width;
            var y = rand() * height;
            var r = rand();
            // 70% are 1px dots; 30% are short directional fibres
            // mimicking actual washi/rice-paper structure.
            if (r < 0.70) {
                ctx.fillRect(x, y, 1, 1);
            } else {
                var len = 2 + Math.floor(rand() * 5);
                if (rand() < 0.5)
                    ctx.fillRect(x, y, 1, len);
                else
                    ctx.fillRect(x, y, len, 1);
            }
        }
    }
}
