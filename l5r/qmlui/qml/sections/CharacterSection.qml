// Copyright (C) 2014-2026 Daniele Simonetti
// Character sheet header: identity (name, clan, family, school, rank,
// XP, insight), traits (5 rings, 8 attributes, void points), social
// flags (honor, glory, status, taint, infamy), the combat strip
// (initiative, armor TN), and the wounds sub-block. QML replacement
// for l5r/ui/tabs/pc_info.py.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../dialogs" as Dialogs
import "../widgets" as Widgets
import Theme 1.0

ColumnLayout {
    id: section
    spacing: Theme.s4

    // Context properties are null on the first binding pass.
    readonly property var _id: pcProxy ? pcProxy : null
    readonly property var _prog: pcProxy ? pcProxy.progression : ({
            "rank": 0,
            "insight": 0,
            "xp": 0,
            "xpLimit": 0,
            "rawXpLimit": 0
        })
    readonly property var _rings: pcProxy ? pcProxy.rings : ({})
    readonly property var _attrs: pcProxy ? pcProxy.attribs : ({})
    readonly property int _voidPoints: pcProxy ? pcProxy.voidPoints : 0
    readonly property var _flags: pcProxy ? pcProxy.flags : ({})
    readonly property var _init: pcProxy ? pcProxy.initiative : ({
            "base": "",
            "mod": "",
            "current": ""
        })
    readonly property var _armor: pcProxy ? pcProxy.armorTn : ({
            "name": "",
            "baseTn": 0,
            "armorTn": 0,
            "armorTnMod": 0,
            "rd": 0,
            "currentTn": 0,
            "desc": ""
        })
    readonly property bool _canEditOrigin: appCtrl ? appCtrl.canEditOrigin() : true

    // A pending rank-up (the root opportunity -- every grant flows from
    // it). Drives the callout below; the matching TOC badge comes from the
    // same proxy. See [[qml-opportunity-surface]].
    readonly property bool _canAdvanceRank: pcProxy ? pcProxy.canAdvanceRank : false

    // Ring / attribute display metadata. Keys mirror the api side
    // (l5r.models.chmodel) so we can index into pcProxy.rings/attribs.
    readonly property var _ringOrder: [{
            "key": "earth",
            "label": qsTr("Earth"),
            "attrs": ["stamina", "willpower"]
        }, {
            "key": "air",
            "label": qsTr("Air"),
            "attrs": ["reflexes", "awareness"]
        }, {
            "key": "water",
            "label": qsTr("Water"),
            "attrs": ["strength", "perception"]
        }, {
            "key": "fire",
            "label": qsTr("Fire"),
            "attrs": ["agility", "intelligence"]
        }]
    readonly property var _voidRow: {
        "key": "void",
        "label": qsTr("Void")
    }
    readonly property var _attrLabels: ({
            "stamina": qsTr("Stamina"),
            "willpower": qsTr("Willpower"),
            "reflexes": qsTr("Reflexes"),
            "awareness": qsTr("Awareness"),
            "strength": qsTr("Strength"),
            "perception": qsTr("Perception"),
            "agility": qsTr("Agility"),
            "intelligence": qsTr("Intelligence")
        })

    readonly property var _flagDefs: [{
            "key": "honor",
            "label": qsTr("Honor")
        }, {
            "key": "glory",
            "label": qsTr("Glory")
        }, {
            "key": "status",
            "label": qsTr("Status")
        }, {
            "key": "taint",
            "label": qsTr("Shadowland Taint")
        }, {
            "key": "infamy",
            "label": qsTr("Infamy")
        }]

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
    Dialogs.AdvanceRankDialog {
        id: advanceRankDlg
        // Multiclass is its own larger flow; the rank-up confirm hands off
        // to the school chooser rather than carrying it inline.
        onRequestJoinSchool: joinSchoolDlg.present()
    }
    Dialogs.JoinSchoolDialog {
        id: joinSchoolDlg
    }

    // The controller gates the rank-up at the outer button: it only opens
    // the dialog once there are no unresolved opportunities left (it emits
    // advanceRankBlocked -> reminder toast otherwise, handled in MainSheet).
    Connections {
        target: appCtrl
        function onAdvanceRankReady() { advanceRankDlg.present(); }
    }

    // -----------------------------------------------------------------
    // Rank-up callout (§6.16 banner). The in-section landing for the
    // Character TOC badge: shows only when a rank-up is waiting. Accent-
    // blue per the positive-action language (crimson is reserved for
    // destructive/unmet), with the 道 path seal and an "Advance Rank" CTA
    // that opens AdvanceRankDialog. This is the ROOT opportunity -- the
    // free kiho / spells / skills grants all follow a rank advancement.
    // -----------------------------------------------------------------
    Rectangle {
        Layout.fillWidth: true
        visible: section._canAdvanceRank
        implicitHeight: 56
        color: Theme.secondarySoft
        border.color: Theme.secondary
        border.width: 1
        radius: 2

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            spacing: 12

            // 36×36 kanji tile (§6.16: smaller than the dialog's 48px).
            Rectangle {
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                Layout.alignment: Qt.AlignVCenter
                radius: 4
                color: Theme.secondary
                Label {
                    anchors.centerIn: parent
                    text: "道"
                    font.family: Theme.fontKanji
                    font.pixelSize: 24
                    color: Theme.whiteWash
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                spacing: 0
                Label {
                    text: qsTr("A NEW RANK AWAITS")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsHeading2
                    font.weight: Theme.wSemiBold
                    font.letterSpacing: 1.4
                    color: Theme.secondary
                }
                Label {
                    text: qsTr("you have an opportunity to decide your destiny")
                    font.family: Theme.fontBody
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.inkMuted
                }
            }

            Widgets.L5RButton {
                text: qsTr("Advance Rank")
                glyph: "道"
                accent: Theme.secondary
                accentDark: Theme.secondaryDark
                Layout.alignment: Qt.AlignVCenter
                // Route through the controller so it can block (with a
                // reminder toast) while opportunities are still pending.
                onClicked: if (appCtrl) appCtrl.requestAdvanceRank()
            }
        }
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
            Label {
                text: qsTr("Name")
            }
            ToolButton {
                text: "♂"
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Random male name")
                onClicked: if (appCtrl)
                    appCtrl.generateName("male")
            }
            ToolButton {
                text: "♀"
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Random female name")
                onClicked: if (appCtrl)
                    appCtrl.generateName("female")
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
                    appCtrl.setName(text);
                }
            }
            // Re-sync if the model changes underneath us (file open, undo).
            Connections {
                target: pcProxy
                function onNameChanged() {
                    if (!nameField.activeFocus && nameField.text !== pcProxy.name) {
                        nameField.text = pcProxy.name;
                    }
                }
            }
        }
        Label {
            text: qsTr("Rank")
            Layout.alignment: Qt.AlignRight
        }
        Label {
            Layout.fillWidth: true
            text: section._prog.rank
            font.family: Theme.fontStat
            font.pixelSize: Theme.fsStatMedium
            font.weight: Theme.wMedium
            font.features: Theme.tabularNumbers
            color: Theme.heading
            elide: Text.ElideRight
        }

        Label {
            text: qsTr("Clan")
        }
        Label {
            Layout.fillWidth: true
            text: (pcProxy && pcProxy.clan) ? pcProxy.clan : qsTr("No Clan")
            elide: Text.ElideRight
        }
        Label {
            text: qsTr("Exp. Points")
            Layout.alignment: Qt.AlignRight
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Label {
                Layout.fillWidth: true
                text: section._prog.xp + " / " + section._prog.xpLimit
                font.family: Theme.fontStat
                font.pixelSize: Theme.fsStatMedium
                font.weight: Theme.wMedium
                color: Theme.heading
                elide: Text.ElideRight
            }
            ToolButton {
                text: "✎"
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Edit XP limit")
                onClicked: expLimitDlg.openWithCurrent()
            }
            ToolButton {
                text: "+"
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Add awarded XP")
                onClicked: addXpDlg.openFresh()
            }
        }

        RowLayout {
            spacing: 4
            Label {
                text: qsTr("Family")
            }
            ToolButton {
                text: "✎"
                enabled: section._canEditOrigin
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Edit character family and clan")
                onClicked: {
                    familyDlg.initialFamilyId = appCtrl ? appCtrl.currentFamilyId() : "";
                    familyDlg.open();
                }
            }
        }
        Label {
            Layout.fillWidth: true
            text: (pcProxy && pcProxy.family) ? pcProxy.family : qsTr("No Family")
            elide: Text.ElideRight
        }
        Label {
            text: qsTr("Insight")
            Layout.alignment: Qt.AlignRight
        }
        Label {
            Layout.fillWidth: true
            text: section._prog.insight
            font.family: Theme.fontStat
            font.pixelSize: Theme.fsStatMedium
            font.weight: Theme.wMedium
            font.features: Theme.tabularNumbers
            color: Theme.heading
            elide: Text.ElideRight
        }

        RowLayout {
            spacing: 4
            Label {
                text: qsTr("School")
            }
            ToolButton {
                text: "✎"
                enabled: section._canEditOrigin
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Edit character first school")
                onClicked: {
                    schoolDlg.initialSchoolId = appCtrl ? appCtrl.currentFirstSchoolId() : "";
                    schoolDlg.open();
                }
            }
        }
        Label {
            Layout.fillWidth: true
            text: (pcProxy && pcProxy.school) ? pcProxy.school : qsTr("No School")
            elide: Text.ElideRight
        }
        Item {
            Layout.preferredWidth: 1
            Layout.preferredHeight: 1
        }
        Item {
            Layout.preferredWidth: 1
            Layout.preferredHeight: 1
        }
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
                        ringKey: modelData.key
                        ringLabel: modelData.label
                        ringValue: section._rings[modelData.key] !== undefined ? section._rings[modelData.key] : 0
                        attrs: modelData.attrs
                        attrLabels: section._attrLabels
                        attrValues: section._attrs
                        onIncreaseTrait: function (traitKey) {
                            if (appCtrl)
                                appCtrl.increaseTrait(traitKey);
                        }
                    }
                }

                Widgets.RingCard {
                    ringKey: "void"
                    ringLabel: section._voidRow.label
                    ringValue: section._rings.void !== undefined ? section._rings.void : 0
                    isVoid: true
                    onIncreaseVoid: if (appCtrl)
                        appCtrl.increaseVoid()
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
                    onValueRequested: function (v) {
                        if (appCtrl)
                            appCtrl.setVoidPoints(v);
                    }
                }
                Item {
                    Layout.fillWidth: true
                }
            }

            // -------------------------------------------------------------
            // Social / spiritual flags -- a sub-block sharing the same
            // parchment as the rings panel (no second border between the
            // two; they are one document, two ledger headings). The
            // inner banner mirrors SheetPanel's own title styling so it
            // reads as a peer to "Rings and Attributes" above.
            // Honor/Glory/Status get the headline treatment (full-width
            // row + 10-dot track); Shadowlands & Infamy sit below a
            // hairline-dashed divider in a compact two-column grid --
            // they're almost always zero in play and don't deserve the
            // same prominence.
            // Click dot sets value, shift+click bumps rank (resets
            // points), scroll fine-tunes by 0.1 and ROLLS OVER at the
            // rank boundary (5.9 -> 6.0, 6.0 -> 5.9; issue #402). The
            // dots carry their tenth digit and the combined N.N score
            // sits big at the left of each track so the rank/decimal
            // split reads at a glance.
            // -------------------------------------------------------------
            Label {
                Layout.fillWidth: true
                Layout.topMargin: 14
                text: qsTr("Social / Spiritual")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsHeading1
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
                text: qsTr("dots are tenths of a rank · click dot to set · scroll to fine-tune (rolls over) · shift+click to advance rank")
                font.italic: true
                font.pixelSize: Theme.fsCaption
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
                    readonly property real _flagValue: section._flags[_key] !== undefined ? section._flags[_key] : 0
                    readonly property int _flagRank: Math.floor(_flagValue)
                    readonly property int _flagPoints: Math.round((_flagValue - _flagRank) * 10)

                    function _commitRank(newRank) {
                        if (!appCtrl)
                            return;
                        var clamped = Math.max(0, Math.min(10, newRank));
                        var combined = clamped + _flagPoints / 10.0;
                        appCtrl.setFlag(_key, combined);
                    }
                    function _commitPoints(newValue) {
                        if (!appCtrl)
                            return;
                        // Points run 0..9 within a rank; the dots edit points
                        // only and never roll the rank over -- use shift+click
                        // (or the −/+ stepper) to change the rank. Clamp
                        // defensively so a stray value can't advance the rank.
                        var pts = Math.max(0, Math.min(9, newValue));
                        var combined = _flagRank + pts / 10.0;
                        if (Math.abs(combined - _flagValue) > 0.001) {
                            appCtrl.setFlag(_key, combined);
                        }
                    }
                    function _bumpRank() {
                        if (!appCtrl)
                            return;
                        if (_flagRank < 10)
                            appCtrl.setFlag(_key, _flagRank + 1);
                    }
                    // Wheel roll-over past the track ends (issue #402):
                    // up from N.9 lands on (N+1).0, down from N.0 on (N-1).9.
                    function _wrapRank(direction) {
                        if (!appCtrl)
                            return;
                        if (direction > 0 && _flagRank < 10)
                            appCtrl.setFlag(_key, _flagRank + 1);
                        else if (direction < 0 && _flagRank > 0)
                            appCtrl.setFlag(_key, (_flagRank - 1) + 0.9);
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
                            font.pixelSize:Theme.fsBody 
                            font.weight: Theme.headingWeight
                            font.letterSpacing: 1.6
                            color: _flagColor
                            Layout.preferredWidth: 100
                            elide: Text.ElideRight
                        }
                        Widgets.RankStepper {
                            value: _flagRank
                            from: 0
                            to: 10
                            onValueModified: function (v) {
                                _commitRank(v);
                            }
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.leftMargin: 20  // align under the label
                        spacing: 10
                        Label {
                            // The actual score, rank.tenths -- the number
                            // the table reads. Stat-sized so it doesn't
                            // fade into the parchment (issue #402).
                            text: _flagRank + "." + _flagPoints
                            font.family: Theme.fontStat
                            font.pixelSize: Theme.fsStatMedium
                            font.weight: Theme.wMedium
                            font.features: Theme.tabularNumbers
                            color: _flagColor
                        }
                        Widgets.PointTrack {
                            Layout.alignment: Qt.AlignVCenter
                            count: 9  // tenths 1..9; wheel rolls the rank over
                            value: _flagPoints
                            accent: _flagColor
                            showDigits: true
                            wrap: true
                            onValueRequested: function (v) {
                                _commitPoints(v);
                            }
                            onRankBumpRequested: _bumpRank()
                            onWrapRequested: function (direction) {
                                _wrapRank(direction);
                            }
                        }
                        Item {
                            Layout.fillWidth: true
                        }
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
                    var ctx = getContext("2d");
                    ctx.reset();
                    ctx.strokeStyle = Theme.borderSubtle;
                    ctx.lineWidth = 1;
                    ctx.setLineDash([4, 4]);
                    ctx.beginPath();
                    ctx.moveTo(0, 0.5);
                    ctx.lineTo(width, 0.5);
                    ctx.stroke();
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
                        readonly property real _flagValue: section._flags[_key] !== undefined ? section._flags[_key] : 0
                        readonly property int _flagRank: Math.floor(_flagValue)
                        readonly property int _flagPoints: Math.round((_flagValue - _flagRank) * 10)

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
                                font.pixelSize: Theme.fsCaption
                                font.weight: Theme.headingWeight
                                font.letterSpacing: 1.4
                                color: _flagColor
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Label {
                                text: _flagRank + "." + _flagPoints
                                font.family: Theme.fontStat
                                font.pixelSize: Theme.fsStatSmall
                                font.features: Theme.tabularNumbers
                                color: _flagColor
                            }
                            Widgets.PointTrack {
                                Layout.alignment: Qt.AlignVCenter
                                count: 9  // tenths 1..9; wheel rolls the rank over
                                dotSize: 10
                                value: _flagPoints
                                accent: _flagColor
                                wrap: true
                                onValueRequested: function (v) {
                                    if (!appCtrl)
                                        return;
                                    // Dots edit the tenths only; the wheel
                                    // (wrap) or shift+click change the rank.
                                    var pts = Math.max(0, Math.min(9, v));
                                    var combined = _flagRank + pts / 10.0;
                                    if (Math.abs(combined - _flagValue) > 0.001) {
                                        appCtrl.setFlag(_key, combined);
                                    }
                                }
                                onRankBumpRequested: {
                                    if (!appCtrl)
                                        return;
                                    if (_flagRank < 10) {
                                        appCtrl.setFlag(_key, _flagRank + 1);
                                    }
                                }
                                onWrapRequested: function (direction) {
                                    if (!appCtrl)
                                        return;
                                    if (direction > 0 && _flagRank < 10)
                                        appCtrl.setFlag(_key, _flagRank + 1);
                                    else if (direction < 0 && _flagRank > 0)
                                        appCtrl.setFlag(_key, (_flagRank - 1) + 0.9);
                                }
                            }
                            Item {
                                Layout.fillWidth: true
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
                    font.pixelSize: Theme.fsCaption
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 2.0
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                    opacity: 0.85
                }
                Label {
                    Layout.fillWidth: true
                    text: section._init.current
                    font.family: Theme.fontStat
                    font.pixelSize: Theme.fsStatLarge
                    font.weight: Theme.wSemiBold
                    font.features: Theme.tabularNumbers
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                }
                Item {
                    Layout.preferredHeight: 4
                }
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("base")
                        font.pixelSize: Theme.fsCaption
                        opacity: 0.65
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    Label {
                        text: section._init.base
                        font.family: Theme.fontStat
                        font.pixelSize: Theme.fsStatSmall
                        font.features: Theme.tabularNumbers
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("mod")
                        font.pixelSize: Theme.fsCaption
                        opacity: 0.65
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    Label {
                        text: section._init.mod
                        font.family: Theme.fontStat
                        font.pixelSize: Theme.fsStatSmall
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
                    font.pixelSize: Theme.fsCaption
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 2.0
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                    opacity: 0.85
                }
                Label {
                    Layout.fillWidth: true
                    text: section._armor.currentTn
                    font.family: Theme.fontStat
                    font.pixelSize: Theme.fsStatLarge
                    font.weight: Theme.wSemiBold
                    font.features: Theme.tabularNumbers
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                }
                Label {
                    Layout.fillWidth: true
                    visible: section._armor.name.length > 0
                    text: section._armor.name
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    horizontalAlignment: Text.AlignHCenter
                    opacity: 0.75
                    elide: Text.ElideRight
                    HoverHandler {
                        id: armorHover
                    }
                    ToolTip.visible: armorHover.hovered && section._armor.desc.length > 0
                    ToolTip.text: section._armor.desc
                }
                Item {
                    Layout.preferredHeight: 2
                }
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("base")
                        font.pixelSize: Theme.fsCaption
                        opacity: 0.65
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    Label {
                        text: section._armor.baseTn
                        font.family: Theme.fontStat
                        font.pixelSize: Theme.fsStatSmall
                        font.features: Theme.tabularNumbers
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("armor")
                        font.pixelSize: Theme.fsCaption
                        opacity: 0.65
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    Label {
                        text: section._armor.armorTn
                        font.family: Theme.fontStat
                        font.pixelSize: Theme.fsStatSmall
                        font.features: Theme.tabularNumbers
                    }
                }
                // Armor-TN modifier ('artn' modifiers). Only shown when
                // non-zero, otherwise base + armor already equals the
                // headline ARMOR TN and the row would be noise.
                RowLayout {
                    Layout.fillWidth: true
                    visible: section._armor.armorTnMod !== 0
                    Label {
                        text: qsTr("mod")
                        font.pixelSize: Theme.fsCaption
                        opacity: 0.65
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    Label {
                        text: (section._armor.armorTnMod > 0 ? "+" : "") + section._armor.armorTnMod
                        font.family: Theme.fontStat
                        font.pixelSize: Theme.fsStatSmall
                        font.features: Theme.tabularNumbers
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        text: qsTr("reduction")
                        font.pixelSize: Theme.fsCaption
                        opacity: 0.65
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    Label {
                        text: section._armor.rd
                        font.family: Theme.fontStat
                        font.pixelSize: Theme.fsStatSmall
                        font.features: Theme.tabularNumbers
                    }
                }
            }

            Item {
                Layout.fillWidth: true
            }
        }
    }

    // -----------------------------------------------------------------
    // Wounds -- full-width sub-block. Replaces the old right-column
    // ladder in the Combat strip. Owns its own header, status banner,
    // and the 4x2 card grid; wired to appCtrl.damageHealth /
    // setWoundsTotal / resetWounds so the dirty flag stays correct.
    // -----------------------------------------------------------------
    Widgets.WoundsBlock {
        Layout.fillWidth: true
    }

    // -----------------------------------------------------------------
    // Inline XP-limit prompt -- avoids QInputDialog (no widget reuse).
    // -----------------------------------------------------------------
    Widgets.L5RDialog {
        id: expLimitDlg
        width: 380
        padding: Theme.s5
        title: qsTr("Set Experience Limit")
        tagline: qsTr("the ceiling the chronicle may spend")
        seal: "経"   // kei -- experience
        accent: Theme.secondary
        accentDark: Theme.secondaryDark
        acceptText: qsTr("Set")

        function openWithCurrent() {
            xpSpin.value = section._prog.rawXpLimit;
            open();
        }
        onAccepted: if (appCtrl)
            appCtrl.setExpLimit(xpSpin.value)

        contentItem: RowLayout {
            spacing: 12
            Label {
                text: qsTr("XP limit")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.headingWeight
                font.letterSpacing: 1.6
                color: Theme.heading
                Layout.alignment: Qt.AlignVCenter
            }
            SpinBox {
                id: xpSpin
                Layout.fillWidth: true
                from: 0
                to: 10000
                editable: true
            }
        }
    }

    // -----------------------------------------------------------------
    // Award-XP prompt -- adds the award on top of the current limit so
    // the user never has to do the math themselves (issue #404).
    // -----------------------------------------------------------------
    Widgets.L5RDialog {
        id: addXpDlg
        width: 380
        padding: Theme.s5
        title: qsTr("Add Experience Points")
        tagline: qsTr("the chronicle rewards its heroes")
        seal: "賞"   // shou -- award
        accent: Theme.secondary
        accentDark: Theme.secondaryDark
        acceptText: qsTr("Add")

        function openFresh() {
            awardSpin.value = 1;
            open();
        }
        onAccepted: if (appCtrl)
            appCtrl.setExpLimit(section._prog.rawXpLimit + awardSpin.value)

        contentItem: RowLayout {
            spacing: 12
            Label {
                text: qsTr("XP awarded")
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.weight: Theme.headingWeight
                font.letterSpacing: 1.6
                color: Theme.heading
                Layout.alignment: Qt.AlignVCenter
            }
            SpinBox {
                id: awardSpin
                Layout.fillWidth: true
                from: 1
                to: 10000
                editable: true
            }
        }
    }
}
