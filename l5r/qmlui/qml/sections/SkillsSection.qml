// Copyright (C) 2014-2026 Daniele Simonetti
// Skills section -- character competencies grouped by their governing
// ring (Earth / Air / Water / Fire / Void). The ring-colour palette
// from Theme is the primary visual hook: every row carries a 4px
// stripe in its ring's hue down the left edge, and the ring banners
// above each cluster repeat that hue at higher saturation. School
// skills -- the ones the character started with via their school --
// are marked with a 2px crimson rib inside the stripe AND rendered
// with an italic name, mirroring how the rulebook bolds them.
// Click a row's name to expand it: the skill description and the
// full mastery-ability ladder appear inline. Unlocked rungs are
// filled circles in the ring colour; locked rungs are hollow and
// dimmed. The legacy second QTableView ("Mastery Abilities") is
// replaced by a footer count -- the data you actually want at hand
// during play is now attached to the skill it belongs to.
// Affordances:
//   - section header "+ New Skill"        --> BuySkillDialog (QML)
//   - per-row "+" inside the emph row     --> emphDlg prompt
//   - per-row "+" at the right edge       --> appCtrl.buySkillRank(id)
// Expected row shape on pcProxy.skills:
//   {
//     id          : string slug
//     name        : string
//     rank        : int     (1..10)
//     trait       : string  (localised display name; used in caption)
//     ringKey     : "earth" | "air" | "water" | "fire" | "void"
//     baseRoll    : "3k2"   (L5R roll-and-keep notation)
//     modRoll     : "3k2"   (post-modifier; falls back to baseRoll)
//     isSchool    : bool
//     emph        : [string, ...]
//     mastery     : [{rank: int, desc: string}, ...]
//     description : string  (optional prose, shown when expanded)
//   }
// Required controller methods on appCtrl:
//   buySkillRank(id)
//   buySkillEmphasis(id, text)
//   availableSkillsToBuy() -> [{id, name, category, trait}, ...]
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../dialogs" as Dialogs
import "../widgets" as Widgets
import Theme 1.0

ColumnLayout {
    id: section
    spacing: Theme.s4

    readonly property var _skills: pcProxy ? pcProxy.skills : []
    readonly property bool _canEdit: !pcProxy || pcProxy.canEdit !== false

    // Pending school-granted wildcard skill/emphasis picks (the datapack's
    // <PlayerChoose>, surfaced as the "skills" opportunity). Drives the
    // callout below; the matching TOC badge comes from the same proxy.
    // See [[qml-opportunity-surface]].
    readonly property int _schoolSkillChoices: pcProxy ? pcProxy.schoolSkillChoiceCount : 0

    // Display order mirrors the Rings & Attributes block in
    // CharacterSection.qml so the eye is already trained for it.
    readonly property var _ringOrder: [{
            "key": "earth",
            "label": qsTr("Earth")
        }, {
            "key": "air",
            "label": qsTr("Air")
        }, {
            "key": "water",
            "label": qsTr("Water")
        }, {
            "key": "fire",
            "label": qsTr("Fire")
        }, {
            "key": "void",
            "label": qsTr("Void")
        }]

    // Id of the currently-expanded skill, or "" for none. A single
    // id (not per-row toggles) so opening a new row collapses the
    // previous one, keeping a long list compact while reading.
    property string _expandedId: ""

    function _toggleExpand(id) {
        _expandedId = (_expandedId === id) ? "" : id;
    }

    function _bucketByRing() {
        var buckets = {
            "earth": [],
            "air": [],
            "water": [],
            "fire": [],
            "void": []
        };
        for (var i = 0; i < _skills.length; ++i) {
            var s = _skills[i];
            var k = ((s && s.ringKey) || "void").toLowerCase();
            if (!buckets[k])
                k = "void";
            buckets[k].push(s);
        }
        for (var key in buckets) {
            buckets[key].sort(function (a, b) {
                    return (a.name || "").localeCompare(b.name || "");
                });
        }
        return buckets;
    }

    readonly property var _buckets: _bucketByRing()

    function _unlockedMasteryCount() {
        var n = 0;
        for (var i = 0; i < _skills.length; ++i) {
            var s = _skills[i];
            if (!s || !s.mastery)
                continue;
            for (var j = 0; j < s.mastery.length; ++j) {
                if (s.mastery[j].rank <= s.rank)
                    n++;
            }
        }
        return n;
    }

    // ----------------------------------------------------------------
    // Inline skill chooser -- replaces the legacy BuyAdvDialog(tag='skill').
    // ----------------------------------------------------------------
    Dialogs.BuySkillDialog {
        id: buySkillDlg
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
    }

    // ----------------------------------------------------------------
    // Inline emphasis-buy prompt -- no QWidget reuse.
    // ----------------------------------------------------------------
    Dialog {
        id: emphDlg
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
        modal: true
        title: qsTr("Buy Skill Emphasis")
        standardButtons: Dialog.Ok | Dialog.Cancel
        width: 380

        property string targetId: ""
        property string targetName: ""

        function openFor(id, name) {
            targetId = id;
            targetName = name;
            emphField.text = "";
            open();
            emphField.forceActiveFocus();
        }
        onAccepted: {
            var t = emphField.text.trim();
            if (appCtrl && t.length > 0)
                appCtrl.buySkillEmphasis(targetId, t);
        }

        contentItem: ColumnLayout {
            spacing: 12
            Label {
                Layout.alignment: Qt.AlignHCenter
                text: qsTr("Emphasis for %1").arg(emphDlg.targetName)
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsHeading1
                color: Theme.heading
            }
            TextField {
                id: emphField
                Layout.fillWidth: true
                placeholderText: qsTr("e.g. Katana, Falconry, Goblin…")
                onAccepted: emphDlg.accept()
            }
        }
    }

    // ----------------------------------------------------------------
    // School-granted skill chooser -- resolves the "skills" opportunity
    // (rank_.skills_to_choose / emphases_to_choose). Replaces the legacy
    // SelWcSkills dialog.
    // ----------------------------------------------------------------
    Dialogs.ChooseSchoolSkillsDialog {
        id: chooseSchoolSkillsDlg
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
    }

    // ----------------------------------------------------------------
    // Opportunity callout (§6.16 banner). The in-section landing for the
    // Skills TOC badge: shows only while the school still owes the player
    // a skill choice. Accent-blue per the positive-action language
    // (crimson is reserved for destructive/unmet), with the 技 skills seal
    // and a "Choose Skills" CTA that opens ChooseSchoolSkillsDialog.
    // ----------------------------------------------------------------
    Rectangle {
        Layout.fillWidth: true
        visible: section._schoolSkillChoices > 0
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
                    text: "技"
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
                    text: qsTr("YOUR SCHOOL GRANTS A CHOICE")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsHeading2
                    font.weight: Theme.wSemiBold
                    font.letterSpacing: 1.4
                    color: Theme.secondary
                }
                Label {
                    text: qsTr("choose the skills your training emphasised")
                    font.family: Theme.fontBody
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.inkMuted
                }
            }

            Widgets.L5RButton {
                text: qsTr("Choose Skills")
                glyph: "技"
                accent: Theme.secondary
                accentDark: Theme.secondaryDark
                enabled: section._canEdit
                Layout.alignment: Qt.AlignVCenter
                onClicked: chooseSchoolSkillsDlg.present()
            }
        }
    }

    // ----------------------------------------------------------------
    // The whole catalogue lives on a single parchment SheetPanel.
    // ----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            // ---- Section header row -------------------------------
            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                Label {
                    text: section._skills.length > 0 ? qsTr("%1 entries").arg(section._skills.length) : qsTr("Your repertoire begins empty.")
                    font.italic: true
                    opacity: 0.7
                }
                Item {
                    Layout.fillWidth: true
                }
                Button {
                    id: newSkillBtn
                    text: qsTr("＋  New Skill")
                    enabled: section._canEdit
                    onClicked: buySkillDlg.open()
                    topPadding: 5
                    bottomPadding: 5
                    leftPadding: 14
                    rightPadding: 14

                    contentItem: Label {
                        text: newSkillBtn.text
                        font.family: Theme.fontDisplay
                        font.pixelSize:Theme.fsBody 
                        font.weight: Theme.headingWeight
                        font.letterSpacing: 1.6
                        color: newSkillBtn.enabled ? Theme.heading : Qt.lighter(Theme.heading, 1.6)
                        opacity: newSkillBtn.hovered ? 1.0 : 0.88
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        // Hairline burnt-gold border with a barely-there
                        // parchment fill that warms on hover -- ink-on-
                        // paper button, not a system rectangle.
                        color: newSkillBtn.down ? Qt.rgba(0.54, 0.35, 0.10, 0.18) : newSkillBtn.hovered ? Qt.rgba(0.54, 0.35, 0.10, 0.10) : "transparent"
                        border.width: 1
                        border.color: newSkillBtn.enabled ? Theme.heading : Theme.borderSubtle
                        radius: 1
                    }
                }
            }

            Widgets.OrnateDivider {
                Layout.fillWidth: true
                ruleColor: Theme.heading
                ruleOpacity: 0.30
            }

            Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignRight
                text: qsTr("click on skill name to see description and mastery")
                font.italic: true
                font.pixelSize: Theme.fsCaption
                opacity: 0.6
            }



            // ---- Ring clusters -----------------------------------
            Repeater {
                model: section._ringOrder
                delegate: ColumnLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 6
                    spacing: 2

                    readonly property string _ringKey: modelData.key
                    readonly property color _ringColor: Theme.ringColor(_ringKey)
                    readonly property var _rows: section._buckets[_ringKey] || []
                    readonly property bool _hasRows: _rows.length > 0

                    // Banner
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Rectangle {
                            Layout.preferredWidth: 18
                            Layout.preferredHeight: 10
                            color: _ringColor
                            opacity: _hasRows ? 1.0 : 0.45
                        }
                        Label {
                            text: modelData.label.toUpperCase()
                            font.family: Theme.fontDisplay
                            font.pixelSize:Theme.fsBody 
                            font.weight: Theme.headingWeight
                            font.letterSpacing: 2.4
                            color: _ringColor
                            opacity: _hasRows ? 1.0 : 0.55
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: _ringColor
                            opacity: 0.30
                        }
                        Label {
                            visible: _hasRows
                            text: _rows.length
                            font.family: Theme.fontStat
                            font.pixelSize: Theme.fsCaption
                            font.features: Theme.tabularNumbers
                            color: _ringColor
                            opacity: 0.85
                        }
                    }
                    // Empty-ring placeholder
                    Label {
                        visible: !_hasRows
                        Layout.fillWidth: true
                        Layout.leftMargin: 28
                        Layout.bottomMargin: 2
                        text: qsTr("— no %1 skills yet —").arg(modelData.label.toLowerCase())
                        font.italic: true
                        font.pixelSize: Theme.fsCaption
                        opacity: 0.45
                    }
                    // Rows
                    Repeater {
                        model: _rows
                        delegate: SkillRow {
                            ringColor: _ringColor
                            row: modelData
                        }
                    }
                }
            }

            // ---- Footer coda --------------------------------------
            Widgets.OrnateDivider {
                Layout.fillWidth: true
                Layout.topMargin: 8
                ruleColor: Theme.heading
                ruleOpacity: 0.30
            }
            Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: qsTr("%1 mastery abilities at hand").arg(section._unlockedMasteryCount())
                font.family: Theme.fontDisplay
                font.pixelSize: Theme.fsCaption
                font.letterSpacing: 2.0
                color: Theme.heading
                opacity: 0.70
            }
        }
    }

    // ----------------------------------------------------------------
    // SkillRow -- one entry. Backed by an Item so we can stack the
    // background tint, the ring stripe, the school notch, and the
    // body layout on top of one another via anchors.
    // ----------------------------------------------------------------
    component SkillRow: Item {
        id: rowItem
        property color ringColor: Theme.accent
        property var row: ({})

        readonly property bool _expanded: section._expandedId === row.id
        readonly property bool _hasMastery: row.mastery && row.mastery.length > 0
        readonly property int _unlockedMastery: {
            if (!_hasMastery)
                return 0;
            var n = 0;
            for (var i = 0; i < row.mastery.length; ++i) {
                if (row.mastery[i].rank <= row.rank)
                    n++;
            }
            return n;
        }

        Layout.fillWidth: true
        implicitHeight: bodyCol.implicitHeight + 8

        HoverHandler {
            id: rowHover
        }

        // Tinted hover/expanded background -- fades in from parchment.
        Rectangle {
            anchors.fill: parent
            color: rowItem.ringColor
            opacity: rowItem._expanded ? 0.09 : (rowHover.hovered ? 0.06 : 0.0)
            Behavior on opacity  {
                NumberAnimation {
                    duration: 120
                }
            }
        }
        // Persistent ring stripe.
        Rectangle {
            id: stripe
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 4
            color: rowItem.ringColor
        }
        // School notch.
        Rectangle {
            visible: rowItem.row.isSchool === true
            anchors.left: stripe.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 2
            color: Theme.accent
            opacity: 0.80
        }

        ColumnLayout {
            id: bodyCol
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.leftMargin: 14
            anchors.rightMargin: 8
            anchors.topMargin: 4
            spacing: 4

            // ---- Top row ---------------------------------------
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                // Name -- italic + crimson for school skills.
                // Click the name to expand the row.
                Label {
                    text: rowItem.row.name || ""
                    color: rowItem.row.isSchool ? Theme.accentMuted : palette.windowText
                    font.italic: rowItem.row.isSchool === true
                    font.weight: rowItem.row.isSchool ? Font.DemiBold : Font.Normal
                    font.pixelSize:Theme.fsBody  + 1
                    Layout.preferredWidth: 180
                    elide: Text.ElideRight
                    TapHandler {
                        onTapped: section._toggleExpand(rowItem.row.id)
                    }
                    HoverHandler {
                        cursorShape: Qt.PointingHandCursor
                    }
                }

                Label {
                    text: (rowItem.row.trait || "").toUpperCase()
                    color: rowItem.ringColor
                    opacity: 0.85
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsCaption
                    font.letterSpacing: 1.4
                    Layout.preferredWidth: 100
                    elide: Text.ElideRight
                }

                // Emphasis pills + "buy emphasis" trigger.
                Flow {
                    Layout.fillWidth: true
                    spacing: 4
                    Repeater {
                        model: rowItem.row.emph || []
                        delegate: Rectangle {
                            radius: 3
                            color: "transparent"
                            border.width: 1
                            border.color: Qt.darker(rowItem.ringColor, 1.2)
                            implicitWidth: pillLabel.implicitWidth + 12
                            implicitHeight: pillLabel.implicitHeight + 4
                            Label {
                                id: pillLabel
                                anchors.centerIn: parent
                                text: modelData
                                font.pixelSize: Theme.fsCaption
                                color: Qt.darker(rowItem.ringColor, 1.2)
                            }
                        }
                    }
                    ToolButton {
                        text: "＋"
                        enabled: section._canEdit
                        flat: true
                        implicitWidth: 22
                        implicitHeight: 18
                        padding: 0
                        font.pixelSize: 12
                        opacity: 0.55
                        palette.buttonText: rowItem.ringColor
                        ToolTip.visible: hovered
                        ToolTip.text: qsTr("Buy a new emphasis")
                        onClicked: emphDlg.openFor(rowItem.row.id, rowItem.row.name)
                    }
                }

                // Roll notation -- the dice you actually shout at the table.
                Label {
                    text: rowItem.row.modRoll || rowItem.row.baseRoll || ""
                    color: Theme.heading
                    font.family: Theme.fontStat
                    font.pixelSize: Theme.fsStatSmall
                    font.weight: Theme.wRegular
                    font.features: Theme.tabularNumbers
                    horizontalAlignment: Text.AlignRight
                    Layout.preferredWidth: 50
                    HoverHandler {
                        id: rollHover
                    }
                    ToolTip.visible: rollHover.hovered && (rowItem.row.baseRoll || "") !== (rowItem.row.modRoll || "")
                    ToolTip.text: qsTr("Base: %1   ·   Mod: %2").arg(rowItem.row.baseRoll || "—").arg(rowItem.row.modRoll || "—")
                }

                // Mastery-unlocked dot -- pre-expansion teaser.
                Rectangle {
                    visible: rowItem._unlockedMastery > 0
                    Layout.preferredWidth: 6
                    Layout.preferredHeight: 6
                    radius: 3
                    color: Theme.heading
                    opacity: 0.85
                    HoverHandler {
                        id: maHover
                    }
                    ToolTip.visible: maHover.hovered
                    ToolTip.text: qsTr("%1 mastery ability unlocked").arg(rowItem._unlockedMastery)
                }

                // Rank -- the hero numeral, tinted to its ring.
                Label {
                    text: rowItem.row.rank !== undefined ? rowItem.row.rank : ""
                    color: rowItem.ringColor
                    font.family: Theme.fontStat
                    font.pixelSize: Theme.fsStatMedium
                    font.weight: Theme.wMedium
                    font.features: Theme.tabularNumbers
                    horizontalAlignment: Text.AlignRight
                    Layout.preferredWidth: 28
                }

                ToolButton {
                    text: "＋"
                    enabled: section._canEdit
                    flat: true
                    implicitWidth: 24
                    implicitHeight: 22
                    padding: 0
                    font.weight: Font.Bold
                    font.pixelSize: 14
                    palette.buttonText: Theme.heading
                    ToolTip.visible: hovered
                    ToolTip.text: qsTr("Buy the next rank in %1").arg(rowItem.row.name)
                    onClicked: if (appCtrl)
                        appCtrl.buySkillRank(rowItem.row.id)
                }
            }

            // ---- Expanded detail (description + mastery ladder) ---
            Item {
                Layout.fillWidth: true
                Layout.topMargin: rowItem._expanded ? 6 : 0
                Layout.bottomMargin: rowItem._expanded ? 4 : 0
                visible: rowItem._expanded
                implicitHeight: visible ? expandedCol.implicitHeight : 0

                ColumnLayout {
                    id: expandedCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: 4
                    spacing: 6

                    Label {
                        visible: !!rowItem.row.description
                        Layout.fillWidth: true
                        text: rowItem.row.description || ""
                        wrapMode: Text.WordWrap
                        textFormat: Text.RichText
                        font.italic: true
                        font.pixelSize: Theme.fsCaption + 1
                        opacity: 0.85
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: rowItem.ringColor
                        opacity: 0.25
                    }
                    Repeater {
                        model: rowItem.row.mastery || []
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            readonly property bool _unlocked: modelData.rank <= rowItem.row.rank

                            Rectangle {
                                Layout.preferredWidth: 18
                                Layout.preferredHeight: 18
                                radius: 9
                                color: _unlocked ? rowItem.ringColor : "transparent"
                                border.width: 1
                                border.color: _unlocked ? Qt.darker(rowItem.ringColor, 1.3) : Theme.borderSubtle
                                Label {
                                    anchors.centerIn: parent
                                    text: modelData.rank
                                    font.family: Theme.fontStat
                                    font.pixelSize: Theme.fsCaption
                                    font.weight: Theme.wRegular
                                    font.features: Theme.tabularNumbers
                                    color: _unlocked ? "white" : Theme.borderStrong
                                }
                            }
                            Label {
                                Layout.fillWidth: true
                                text: modelData.desc
                                wrapMode: Text.WordWrap
                                color: _unlocked ? palette.windowText : Qt.lighter(palette.windowText, 1.8)
                                opacity: _unlocked ? 1.0 : 0.55
                                font.italic: !_unlocked
                            }
                        }
                    }
                    Label {
                        visible: !rowItem._hasMastery
                        Layout.fillWidth: true
                        Layout.leftMargin: 22
                        text: qsTr("This skill has no mastery abilities.")
                        font.italic: true
                        font.pixelSize: Theme.fsCaption
                        opacity: 0.55
                    }
                }
            }
        }
    }
}
