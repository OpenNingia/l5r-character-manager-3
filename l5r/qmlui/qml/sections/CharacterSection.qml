// Copyright (C) 2014-2026 Daniele Simonetti
// Character sheet header: identity (name, clan, family, school, rank,
// XP, insight), traits (5 rings, 8 attributes, void points), social
// flags (honor, glory, status, taint, infamy), and the combat strip
// (initiative, armor TN, wound table). QML replacement for
// l5r/ui/tabs/pc_info.py.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../dialogs" as Dialogs
import "../widgets" as Widgets

import Theme 1.0

ColumnLayout {
    id: section
    spacing: Theme.sectionSpacing

    // Context properties are null on the first binding pass.
    readonly property var _id: pcProxy ? pcProxy : null
    readonly property var _prog: pcProxy ? pcProxy.progression
        : ({ rank: 0, insight: 0, xp: 0, xpLimit: 0, rawXpLimit: 0 })
    readonly property var _rings: pcProxy ? pcProxy.rings : ({})
    readonly property var _attrs: pcProxy ? pcProxy.attribs : ({})
    readonly property int _voidPoints: pcProxy ? pcProxy.voidPoints : 0
    readonly property var _flags: pcProxy ? pcProxy.flags : ({})
    readonly property var _init: pcProxy ? pcProxy.initiative
        : ({ base: "", mod: "", current: "" })
    readonly property var _armor: pcProxy ? pcProxy.armorTn
        : ({ name: "", baseTn: 0, armorTn: 0, rd: 0, currentTn: 0, desc: "" })
    readonly property var _wounds: pcProxy ? pcProxy.wounds : []
    readonly property int _hm: pcProxy ? pcProxy.healthMultiplier : 2
    // The highest row in the wound table that has any wounds recorded
    // against it is the player's current wound level -- `taken` is the
    // cumulative wounds at-or-below that threshold, so the last row
    // with taken > 0 is the active row. Defaults to 0 (Healthy) when
    // no wounds have been taken yet.
    readonly property int _currentWoundIndex: {
        var last = 0
        if (_wounds) {
            for (var i = 0; i < _wounds.length; ++i) {
                if (_wounds[i].taken > 0) last = i
            }
        }
        return last
    }
    readonly property bool _canEditOrigin: appCtrl ? appCtrl.canEditOrigin() : true

    // Ring / attribute display metadata. Keys mirror the api side
    // (l5r.models.chmodel) so we can index into pcProxy.rings/attribs.
    readonly property var _ringOrder: [
        { key: "earth", label: qsTr("Earth"),
          attrs: ["stamina", "willpower"] },
        { key: "air",   label: qsTr("Air"),
          attrs: ["reflexes", "awareness"] },
        { key: "water", label: qsTr("Water"),
          attrs: ["strength", "perception"] },
        { key: "fire",  label: qsTr("Fire"),
          attrs: ["agility", "intelligence"] }
    ]
    readonly property var _voidRow: { "key": "void", "label": qsTr("Void") }
    readonly property var _attrLabels: ({
        "stamina":      qsTr("Stamina"),
        "willpower":    qsTr("Willpower"),
        "reflexes":     qsTr("Reflexes"),
        "awareness":    qsTr("Awareness"),
        "strength":     qsTr("Strength"),
        "perception":   qsTr("Perception"),
        "agility":      qsTr("Agility"),
        "intelligence": qsTr("Intelligence")
    })

    readonly property var _flagDefs: [
        { key: "honor",  label: qsTr("Honor") },
        { key: "glory",  label: qsTr("Glory") },
        { key: "status", label: qsTr("Status") },
        { key: "taint",  label: qsTr("Shadowland Taint") },
        { key: "infamy", label: qsTr("Infamy") }
    ]

    Dialogs.FamilyChooserDialog {
        id: familyDlg
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
    }
    Dialogs.FirstSchoolChooserDialog {
        id: schoolDlg
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
    }

    // -----------------------------------------------------------------
    // Identity row: name + clan/family/school + rank/XP/insight
    // -----------------------------------------------------------------
    GridLayout {
        Layout.fillWidth: true
        columns: 4
        columnSpacing: 14
        rowSpacing: 6

        // Column 0 — labels (with adornments)
        RowLayout {
            spacing: 4
            Label { text: qsTr("Name") }
            ToolButton {
                text: "♂"
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Random male name")
                onClicked: if (appCtrl) appCtrl.generateName("male")
            }
            ToolButton {
                text: "♀"
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Random female name")
                onClicked: if (appCtrl) appCtrl.generateName("female")
            }
        }
        TextField {
            id: nameField
            Layout.fillWidth: true
            Layout.columnSpan: 1
            text: pcProxy ? pcProxy.name : ""
            placeholderText: qsTr("Character name")
            onEditingFinished: {
                if (appCtrl && text !== (pcProxy ? pcProxy.name : "")) {
                    appCtrl.setName(text)
                }
            }
            // Re-sync if the model changes underneath us (file open, undo).
            Connections {
                target: pcProxy
                function onNameChanged() {
                    if (!nameField.activeFocus && nameField.text !== pcProxy.name) {
                        nameField.text = pcProxy.name
                    }
                }
            }
        }
        Label { text: qsTr("Rank"); Layout.alignment: Qt.AlignRight }
        Label {
            Layout.fillWidth: true
            text: section._prog.rank
            font.family: Theme.fontDisplay
            font.pixelSize: 16
            font.weight: Font.DemiBold
            font.features: Theme.tabularNumbers
            color: Theme.heading
            elide: Text.ElideRight
        }

        Label { text: qsTr("Clan") }
        Label {
            Layout.fillWidth: true
            text: (pcProxy && pcProxy.clan) ? pcProxy.clan : qsTr("No Clan")
            elide: Text.ElideRight
        }
        Label { text: qsTr("Exp. Points"); Layout.alignment: Qt.AlignRight }
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Label {
                Layout.fillWidth: true
                text: section._prog.xp + " / " + section._prog.xpLimit
                font.family: Theme.fontDisplay
                font.pixelSize: 16
                font.weight: Font.DemiBold
                color: Theme.heading
                elide: Text.ElideRight
            }
            ToolButton {
                text: "✎"
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Edit XP limit")
                onClicked: expLimitDlg.openWithCurrent()
            }
        }

        RowLayout {
            spacing: 4
            Label { text: qsTr("Family") }
            ToolButton {
                text: "✎"
                enabled: section._canEditOrigin
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Edit character family and clan")
                onClicked: {
                    familyDlg.initialFamilyId = appCtrl ? appCtrl.currentFamilyId() : ""
                    familyDlg.open()
                }
            }
        }
        Label {
            Layout.fillWidth: true
            text: (pcProxy && pcProxy.family) ? pcProxy.family : qsTr("No Family")
            elide: Text.ElideRight
        }
        Label { text: qsTr("Insight"); Layout.alignment: Qt.AlignRight }
        Label {
            Layout.fillWidth: true
            text: section._prog.insight
            font.family: Theme.fontDisplay
            font.pixelSize: 16
            font.weight: Font.DemiBold
            font.features: Theme.tabularNumbers
            color: Theme.heading
            elide: Text.ElideRight
        }

        RowLayout {
            spacing: 4
            Label { text: qsTr("School") }
            ToolButton {
                text: "✎"
                enabled: section._canEditOrigin
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Edit character first school")
                onClicked: {
                    schoolDlg.initialSchoolId = appCtrl ? appCtrl.currentFirstSchoolId() : ""
                    schoolDlg.open()
                }
            }
        }
        Label {
            Layout.fillWidth: true
            text: (pcProxy && pcProxy.school) ? pcProxy.school : qsTr("No School")
            elide: Text.ElideRight
        }
        Item { Layout.preferredWidth: 1; Layout.preferredHeight: 1 }
        Item { Layout.preferredWidth: 1; Layout.preferredHeight: 1 }
    }

    // -----------------------------------------------------------------
    // Rings & attributes: five horizontal cards (Earth/Air/Water/Fire/
    // Void), each tinted in its element colour. The 4 elemental cards
    // host two attribute rows; the Void card is buy-rank-only and
    // pairs with the Void-points dot track underneath.
    // -----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Rings and Attributes")

        ColumnLayout {
            width: parent.width
            spacing: 10

            Flow {
                Layout.fillWidth: true
                spacing: 10

                Repeater {
                    model: section._ringOrder
                    delegate: Widgets.RingCard {
                        ringKey:    modelData.key
                        ringLabel:  modelData.label
                        ringValue:  section._rings[modelData.key] !== undefined
                            ? section._rings[modelData.key] : 0
                        attrs:      modelData.attrs
                        attrLabels: section._attrLabels
                        attrValues: section._attrs
                        onIncreaseTrait: function(traitKey) {
                            if (appCtrl) appCtrl.increaseTrait(traitKey)
                        }
                    }
                }

                Widgets.RingCard {
                    ringKey:   "void"
                    ringLabel: section._voidRow.label
                    ringValue: section._rings.void !== undefined
                        ? section._rings.void : 0
                    isVoid: true
                    onIncreaseVoid: if (appCtrl) appCtrl.increaseVoid()
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 4
                spacing: 10
                Label {
                    text: qsTr("Void Points")
                    font.weight: Font.DemiBold
                    color: Theme.ringVoid
                }
                Widgets.PointTrack {
                    count: 10
                    value: section._voidPoints
                    accent: Theme.ringVoid
                    onValueChanged: {
                        if (appCtrl && value !== section._voidPoints) {
                            appCtrl.setVoidPoints(value)
                        }
                    }
                }
                Item { Layout.fillWidth: true }
            }

            // -------------------------------------------------------------
            // Social / spiritual flags -- a sub-block sharing the same
            // parchment as the rings panel (no second border between the
            // two; they are one document, two ledger headings). The
            // inner banner mirrors SheetPanel's own title styling so it
            // reads as a peer to "Rings and Attributes" above.
            //
            // Honor/Glory/Status get the headline treatment (full-width
            // row + 10-dot track); Shadowlands & Infamy sit below a
            // hairline-dashed divider in a compact two-column grid --
            // they're almost always zero in play and don't deserve the
            // same prominence.
            //
            // Click dot sets value, shift+click bumps rank (resets
            // points), scroll fine-tunes by 1. Shift+click and clicking
            // the 10th dot both route through setFlag(rank+1) -- when
            // the model pushes back the value binding resets the dots
            // to 0 naturally.
            // -------------------------------------------------------------
            Label {
                Layout.fillWidth: true
                Layout.topMargin: 14
                text: qsTr("Social / Spiritual")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.titleFont
                font.weight: Theme.headingWeight
                font.letterSpacing: 1.5
                color: Theme.heading
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.topMargin: -2
                Layout.preferredHeight: 1
                color: Theme.heading
                opacity: 0.45
            }

            Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignRight
                text: qsTr("click dot to set · shift+click to advance rank · scroll to fine-tune")
                font.italic: true
                font.pixelSize: Theme.smallFont
                opacity: 0.6
            }

            // ---- Honor / Glory / Status -- full-width tracks --------
            Repeater {
                model: [section._flagDefs[0], section._flagDefs[1], section._flagDefs[2]]
                delegate: ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    readonly property string _key: modelData.key
                    readonly property color _flagColor: Theme.flagColor(_key)
                    readonly property real _flagValue:
                        section._flags[_key] !== undefined
                            ? section._flags[_key] : 0
                    readonly property int _flagRank: Math.floor(_flagValue)
                    readonly property int _flagPoints:
                        Math.round((_flagValue - _flagRank) * 10)

                    function _commitRank(newRank) {
                        if (!appCtrl) return
                        var clamped = Math.max(0, Math.min(10, newRank))
                        var combined = clamped + _flagPoints / 10.0
                        appCtrl.setFlag(_key, combined)
                    }
                    function _commitPoints(newValue) {
                        if (!appCtrl) return
                        if (newValue === 10) {
                            // 10th dot = rank-up, points reset to 0.
                            if (_flagRank < 10) appCtrl.setFlag(_key, _flagRank + 1)
                            return
                        }
                        var combined = _flagRank + newValue / 10.0
                        if (Math.abs(combined - _flagValue) > 0.001) {
                            appCtrl.setFlag(_key, combined)
                        }
                    }
                    function _bumpRank() {
                        if (!appCtrl) return
                        if (_flagRank < 10) appCtrl.setFlag(_key, _flagRank + 1)
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        Rectangle {
                            Layout.preferredWidth: 10
                            Layout.preferredHeight: 10
                            radius: 5
                            color: _flagColor
                        }
                        Label {
                            text: modelData.label.toUpperCase()
                            font.family: Theme.fontDisplay
                            font.pixelSize: Theme.bodyFont
                            font.weight: Theme.headingWeight
                            font.letterSpacing: 1.6
                            color: _flagColor
                            Layout.preferredWidth: 100
                            elide: Text.ElideRight
                        }
                        Widgets.RankStepper {
                            value: _flagRank
                            from: 0; to: 10
                            onValueModified: function(v) { _commitRank(v) }
                        }
                        Item { Layout.fillWidth: true }
                        Label {
                            text: qsTr("rank ") + _flagRank + "." + _flagPoints
                            font.pixelSize: Theme.smallFont
                            font.features: Theme.tabularNumbers
                            color: _flagColor
                            opacity: 0.9
                        }
                    }
                    Widgets.PointTrack {
                        Layout.leftMargin: 20  // align under the label
                        count: 10
                        value: _flagPoints
                        accent: _flagColor
                        onValueChanged: _commitPoints(value)
                        onRankBumpRequested: _bumpRank()
                    }
                }
            }

            // ---- Hairline dashed divider ----------------------------
            Canvas {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                Layout.topMargin: 6
                Layout.bottomMargin: 6
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.reset()
                    ctx.strokeStyle = Theme.borderSubtle
                    ctx.lineWidth = 1
                    ctx.setLineDash([4, 4])
                    ctx.beginPath()
                    ctx.moveTo(0, 0.5)
                    ctx.lineTo(width, 0.5)
                    ctx.stroke()
                }
                onWidthChanged: requestPaint()
            }

            // ---- Shadowlands / Infamy -- compact two-column grid ----
            GridLayout {
                Layout.fillWidth: true
                columns: 2
                columnSpacing: 24
                rowSpacing: 4

                Repeater {
                    model: [section._flagDefs[3], section._flagDefs[4]]
                    delegate: ColumnLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignTop
                        spacing: 4
                        readonly property string _key: modelData.key
                        readonly property color _flagColor: Theme.flagColor(_key)
                        readonly property real _flagValue:
                            section._flags[_key] !== undefined
                                ? section._flags[_key] : 0
                        readonly property int _flagRank: Math.floor(_flagValue)
                        readonly property int _flagPoints:
                            Math.round((_flagValue - _flagRank) * 10)

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Rectangle {
                                Layout.preferredWidth: 10
                                Layout.preferredHeight: 10
                                radius: 5
                                color: _flagColor
                            }
                            Label {
                                text: modelData.label.toUpperCase()
                                font.family: Theme.fontDisplay
                                font.pixelSize: Theme.smallFont
                                font.weight: Theme.headingWeight
                                font.letterSpacing: 1.4
                                color: _flagColor
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }
                            Label {
                                text: _flagRank + "." + _flagPoints
                                font.pixelSize: Theme.smallFont
                                font.features: Theme.tabularNumbers
                                color: _flagColor
                                opacity: 0.9
                            }
                        }
                        Widgets.PointTrack {
                            count: 10
                            dotSize: 10
                            value: _flagPoints
                            accent: _flagColor
                            onValueChanged: {
                                if (!appCtrl) return
                                if (value === 10) {
                                    if (_flagRank < 10) {
                                        appCtrl.setFlag(_key, _flagRank + 1)
                                    }
                                    return
                                }
                                var combined = _flagRank + value / 10.0
                                if (Math.abs(combined - _flagValue) > 0.001) {
                                    appCtrl.setFlag(_key, combined)
                                }
                            }
                            onRankBumpRequested: {
                                if (!appCtrl) return
                                if (_flagRank < 10) {
                                    appCtrl.setFlag(_key, _flagRank + 1)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // -----------------------------------------------------------------
    // Combat Bar: a single panel with three columns -- Initiative,
    // Armor TN, Wounds. The first two columns lead with a large hero
    // number (the value the player actually reads at the table) and
    // demote base/modifier/armor/reduction to caption rows underneath.
    // The Wounds column is a vertical ladder (Healthy at the top,
    // Out at the bottom) with a burnt-gold stripe marking the
    // player's current level -- closer to how the wound system reads
    // in the L5R 4e rulebook than the old 4x2 grid.
    // -----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Combat")

        RowLayout {
            width: parent.width
            spacing: 20

            // ---- Initiative column ----------------------------------
            ColumnLayout {
                Layout.preferredWidth: 140
                Layout.alignment: Qt.AlignTop
                spacing: 4

                Label {
                    Layout.fillWidth: true
                    text: qsTr("INITIATIVE")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.smallFont
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 2.0
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                    opacity: 0.85
                }
                Label {
                    Layout.fillWidth: true
                    text: section._init.current
                    font.family: Theme.fontDisplay
                    font.pixelSize: 30
                    font.weight: Font.Bold
                    font.features: Theme.tabularNumbers
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                }
                Item { Layout.preferredHeight: 4 }
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("base")
                        font.pixelSize: Theme.smallFont
                        opacity: 0.65
                    }
                    Item { Layout.fillWidth: true }
                    Label {
                        text: section._init.base
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.bodyFont
                        font.features: Theme.tabularNumbers
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("mod")
                        font.pixelSize: Theme.smallFont
                        opacity: 0.65
                    }
                    Item { Layout.fillWidth: true }
                    Label {
                        text: section._init.mod
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.bodyFont
                        font.features: Theme.tabularNumbers
                    }
                }
            }

            // Vertical divider in the burnt-gold rule colour, faded
            // so it reads as a hairline rather than a hard pipe.
            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                Layout.topMargin: 4
                Layout.bottomMargin: 4
                color: Theme.heading
                opacity: 0.25
            }

            // ---- Armor TN column ------------------------------------
            ColumnLayout {
                Layout.preferredWidth: 160
                Layout.alignment: Qt.AlignTop
                spacing: 4

                Label {
                    Layout.fillWidth: true
                    text: qsTr("ARMOR TN")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.smallFont
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 2.0
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                    opacity: 0.85
                }
                Label {
                    Layout.fillWidth: true
                    text: section._armor.currentTn
                    font.family: Theme.fontDisplay
                    font.pixelSize: 30
                    font.weight: Font.Bold
                    font.features: Theme.tabularNumbers
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                }
                Label {
                    Layout.fillWidth: true
                    visible: section._armor.name.length > 0
                    text: section._armor.name
                    font.italic: true
                    font.pixelSize: Theme.smallFont
                    horizontalAlignment: Text.AlignHCenter
                    opacity: 0.75
                    elide: Text.ElideRight
                    HoverHandler { id: armorHover }
                    ToolTip.visible: armorHover.hovered && section._armor.desc.length > 0
                    ToolTip.text: section._armor.desc
                }
                Item { Layout.preferredHeight: 2 }
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("base")
                        font.pixelSize: Theme.smallFont
                        opacity: 0.65
                    }
                    Item { Layout.fillWidth: true }
                    Label {
                        text: section._armor.baseTn
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.bodyFont
                        font.features: Theme.tabularNumbers
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("armor")
                        font.pixelSize: Theme.smallFont
                        opacity: 0.65
                    }
                    Item { Layout.fillWidth: true }
                    Label {
                        text: section._armor.armorTn
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.bodyFont
                        font.features: Theme.tabularNumbers
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("reduction")
                        font.pixelSize: Theme.smallFont
                        opacity: 0.65
                    }
                    Item { Layout.fillWidth: true }
                    Label {
                        text: section._armor.rd
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.bodyFont
                        font.features: Theme.tabularNumbers
                    }
                }
            }

            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                Layout.topMargin: 4
                Layout.bottomMargin: 4
                color: Theme.heading
                opacity: 0.25
            }

            // ---- Wounds ladder --------------------------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                spacing: 1

                Label {
                    Layout.fillWidth: true
                    text: qsTr("WOUNDS  ×%1").arg(section._hm)
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.smallFont
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 2.0
                    color: Theme.heading
                    opacity: 0.85
                }
                Item { Layout.preferredHeight: 2 }
                Repeater {
                    model: section._wounds
                    delegate: RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        // The "active" row is the player's current
                        // wound level. Inactive rows render in the
                        // panel's body ink colour at normal weight;
                        // the active row gets a 3px burnt-gold
                        // stripe on the left, plus heading colour
                        // + DemiBold weight on the text.
                        readonly property bool _active:
                            index === section._currentWoundIndex

                        Rectangle {
                            Layout.preferredWidth: 3
                            Layout.fillHeight: true
                            color: _active ? Theme.heading : "transparent"
                        }
                        Label {
                            text: modelData.label
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            font.weight: _active ? Font.DemiBold : Font.Normal
                            color: _active ? Theme.heading : palette.windowText
                        }
                        Label {
                            text: modelData.value
                            Layout.preferredWidth: 32
                            horizontalAlignment: Text.AlignRight
                            font.family: Theme.fontDisplay
                            font.weight: _active ? Font.DemiBold : Font.Normal
                            font.features: Theme.tabularNumbers
                            color: _active ? Theme.heading : palette.windowText
                        }
                        Label {
                            text: modelData.taken ? modelData.taken : ""
                            Layout.preferredWidth: 28
                            horizontalAlignment: Text.AlignRight
                            font.pixelSize: Theme.smallFont
                            font.features: Theme.tabularNumbers
                            opacity: 0.6
                        }
                    }
                }
            }
        }
    }

    // -----------------------------------------------------------------
    // Inline XP-limit prompt -- avoids QInputDialog (no widget reuse).
    // -----------------------------------------------------------------
    Dialog {
        id: expLimitDlg
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
        modal: true
        title: qsTr("Set Experience Limit")
        standardButtons: Dialog.Ok | Dialog.Cancel

        function openWithCurrent() {
            xpSpin.value = section._prog.rawXpLimit
            open()
        }
        onAccepted: if (appCtrl) appCtrl.setExpLimit(xpSpin.value)

        contentItem: ColumnLayout {
            spacing: 10
            Label { text: qsTr("XP limit:"); Layout.alignment: Qt.AlignHCenter }
            SpinBox {
                id: xpSpin
                Layout.alignment: Qt.AlignHCenter
                from: 0
                to: 10000
                editable: true
            }
        }
    }
}
