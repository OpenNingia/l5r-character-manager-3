// Copyright (C) 2014-2026 Daniele Simonetti
// Design-system dropdown (§6.7). Bakes the parchment skin -- cream fill,
// hairline border, brush caret, parchment popup, accent-tinted hover --
// that BuySkillDialog and InscribePerkDialog each hand-rolled. Consumers
// use it like a normal ComboBox (model / textRole / currentIndex /
// onActivated); `accent` tints the focus border and popup highlight
// (crimson by default; pass Theme.secondary for blue/Blessing contexts).
//
// Display text is Cinzel (--text-label, §6.7) so it can carry weight;
// popup items are body (IM Fell, wRegular -- never faux-bold per §3.4).
//
// Usage:
//   Widgets.L5RComboBox {
//       textRole: "name"; model: candidates; accent: Theme.secondary
//       onActivated: (i) => { ... }
//   }
import QtQuick
import QtQuick.Controls
import Theme 1.0

ComboBox {
    id: combo
    property color accent: Theme.accent

    implicitHeight: 36

    background: Rectangle {
        color: Theme.parchmentBase
        border.color: combo.activeFocus ? combo.accent : Theme.borderSubtle
        border.width: 1
        radius: 2
    }

    contentItem: Label {
        leftPadding: 10
        rightPadding: combo.indicator.width + 6
        text: combo.displayText
        font.family: Theme.fontDisplay
        font.pixelSize: Theme.fsLabel
        font.weight: Theme.wSemiBold
        color: Theme.ink
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    // Brush caret in place of the OS pixmap (8px triangle, §6.7).
    indicator: Label {
        x: combo.width - width - 10
        y: (combo.height - height) / 2
        text: "▾"
        font.pixelSize: 12
        color: Theme.inkMuted
        opacity: combo.pressed ? 1.0 : 0.85
    }

    popup: Popup {
        y: combo.height
        width: combo.width
        implicitHeight: Math.min(contentItem.implicitHeight + 4, 320)
        padding: 2
        background: Rectangle {
            color: Theme.whiteWash
            border.color: Theme.borderSubtle
            border.width: 1
            radius: 2
        }
        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: combo.popup.visible ? combo.delegateModel : null
            currentIndex: combo.highlightedIndex
            ScrollIndicator.vertical: ScrollIndicator {}
        }
    }

    delegate: ItemDelegate {
        width: combo.width
        implicitHeight: 32
        highlighted: combo.highlightedIndex === index
        background: Rectangle {
            // Light accent wash on hover/highlight (§6.7); the explicit
            // crimson/blue -bg tokens are for fixed-accent screens, so we
            // derive from `accent` to follow whatever the combo is themed.
            color: highlighted ? Qt.rgba(combo.accent.r, combo.accent.g, combo.accent.b, 0.13) : "transparent"
        }
        contentItem: Label {
            leftPadding: 12
            rightPadding: 6
            text: combo.textRole.length > 0 ? modelData[combo.textRole] : modelData
            font.family: Theme.fontBody
            font.pixelSize: Theme.fsBody
            color: Theme.ink
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }
}
