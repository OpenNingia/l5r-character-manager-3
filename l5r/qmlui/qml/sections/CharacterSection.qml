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

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        color: Theme.divider; opacity: Theme.dividerOpacity
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
        }
    }

    // -----------------------------------------------------------------
    // Social / spiritual flags -- their own full-width row beneath the
    // rings. Five compact columns laid out horizontally; each column
    // shows the flag name, a rank SpinBox, and a 0..9 point track in
    // the flag's brand colour.
    // -----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Social / Spiritual")

        Flow {
            width: parent.width
            spacing: 16

            Repeater {
                model: section._flagDefs
                delegate: ColumnLayout {
                    width: 160
                    spacing: 4
                    readonly property color _flagColor: Theme.flagColor(modelData.key)
                    readonly property real _flagValue:
                        section._flags[modelData.key] !== undefined
                            ? section._flags[modelData.key] : 0
                    readonly property int _flagRank:
                        Math.floor(_flagValue)
                    readonly property int _flagPoints:
                        Math.round((_flagValue - _flagRank) * 10)

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Rectangle {
                            width: 10; height: 10; radius: 5
                            color: _flagColor
                            border.width: 1
                            border.color: Qt.darker(color, 1.3)
                        }
                        Label {
                            text: modelData.label
                            font.weight: Font.DemiBold
                            color: _flagColor
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }
                        SpinBox {
                            from: 0; to: 10
                            value: _flagRank
                            implicitWidth: 60
                            onValueModified: {
                                if (!appCtrl) return
                                var combined = value + _flagPoints / 10.0
                                appCtrl.setFlag(modelData.key, combined)
                            }
                        }
                    }
                    Widgets.PointTrack {
                        Layout.alignment: Qt.AlignLeft
                        count: 9
                        value: _flagPoints
                        accent: _flagColor
                        onValueChanged: {
                            if (!appCtrl) return
                            var combined = _flagRank + value / 10.0
                            if (Math.abs(combined - _flagValue) > 0.001) {
                                appCtrl.setFlag(modelData.key, combined)
                            }
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 1
        color: Theme.divider; opacity: Theme.dividerOpacity
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
