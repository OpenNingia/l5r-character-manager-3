// Copyright (C) 2014-2026 Daniele Simonetti
// Miscellanea section (雑 -- zatsu, "the sundries") -- merges the legacy
// l5r/ui/tabs/equipment.py (gear + coin) and l5r/ui/tabs/modifiers.py
// (custom roll/stat modifiers) into one page, per the QML taxonomy.
//
// Design intent: "The Traveler's Effects." Two registers stack down the
// page. First the pack: the gear the samurai carries -- the school's
// starting outfit set down first (quietly sealed as school-granted), the
// player's own additions beneath, and at the foot the coin purse (koku /
// bu / zeni) that travelled with the legacy equipment tab. Then the
// edges: the custom modifiers the character brings to a roll, each a card
// stating what it bends, by how much, and why -- with a switch to declare
// whether it is in play right now. An unapplied modifier reads greyed, so
// the page shows at a glance which edges are live.
//
// Adding/editing a modifier opens ModifierDialog (QML-native). Gear is
// edited inline (each row is a text field); coin commits on edit.
//
// Data contract expected from the proxy (degrades to the empty-state):
//   pcProxy.equipment: [
//     { kind: "starting" | "personal", index: int, text: str,
//       isStarting: bool }, ... ]                     // school first
//   pcProxy.money: { koku: int, bu: int, zeni: int }
//   pcProxy.modifiers: [
//     { id: "0x…",          // session-stable; keys edit/remove/toggle
//       type: "atkr",        // MOD_TYPES key
//       detail: "Katana",    // may be ""
//       value: "+2",         // roll-and-keep + bonus string
//       reason: "…",         // player's note; may be ""
//       active: true }, ... ]
// Required controller members on appCtrl:
//   addEquipment(text)                         removeEquipment(kind, index)
//   setEquipmentText(kind, index, text)        setMoney(koku, bu, zeni)
//   modifierTypes() -> [{ key, label, detailKind, detailLabel }]
//   addModifier(type, detail, value, reason, active)
//   editModifier(id, type, detail, value, reason, active)
//   setModifierActive(id, active)              removeModifier(id)
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../dialogs" as Dialogs
import "../widgets" as Widgets
import Theme 1.0

ColumnLayout {
    id: section
    spacing: Theme.s4

    // -----------------------------------------------------------------
    // Defensive bindings -- the proxy may be null on first paint or under
    // the offscreen preview tool (which binds a null pcProxy/appCtrl).
    // -----------------------------------------------------------------
    readonly property var _equipment: (pcProxy && pcProxy.equipment) ? pcProxy.equipment : []
    readonly property var _money: (pcProxy && pcProxy.money) ? pcProxy.money : ({
                                                                                    "koku": 0,
                                                                                    "bu": 0,
                                                                                    "zeni": 0
                                                                                })
    readonly property var _modifiers: (pcProxy && pcProxy.modifiers) ? pcProxy.modifiers : []
    readonly property bool _hasEquipment: section._equipment.length > 0
    readonly property bool _hasModifiers: section._modifiers.length > 0

    // Modifier kinds, fetched once (the table is static app config). Used
    // to turn a row's `type` key back into its human label.
    readonly property var _modifierTypes: (appCtrl && appCtrl.modifierTypes) ? (appCtrl.modifierTypes() || []) : []
    function _typeLabel(key) {
        for (var i = 0; i < section._modifierTypes.length; ++i) {
            if (section._modifierTypes[i].key === key)
                return section._modifierTypes[i].label;
        }
        return key || "";
    }

    function _commitEquipment(item, text) {
        if (item && appCtrl)
            appCtrl.setEquipmentText(item.kind, item.index, text);
    }
    function _removeEquipment(item) {
        if (item && appCtrl)
            appCtrl.removeEquipment(item.kind, item.index);
    }
    function _removeModifier(item) {
        if (item && appCtrl)
            appCtrl.removeModifier(item.id);
    }

    // -----------------------------------------------------------------
    // Dialog -- authored fresh in QML (no QWidget reuse).
    // -----------------------------------------------------------------
    Dialogs.ModifierDialog {
        id: modifierDlg
    }

    // =================================================================
    // Register one -- THE PACK (gear + coin).
    // =================================================================
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Equipment")

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            // ---- Header row: subtitle + count + add affordance -------
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: -4
                spacing: Theme.s2

                Label {
                    text: qsTr("the gear you carry into the field")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.6
                }
                Item {
                    Layout.fillWidth: true
                }
                Label {
                    visible: section._hasEquipment
                    text: section._equipment.length === 1 ? qsTr("1 item") : qsTr("%1 items").arg(section._equipment.length)
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.55
                }
                AddAffordance {
                    text: qsTr("＋  Add Item")
                    onTriggered: {
                        if (appCtrl)
                            appCtrl.addEquipment("");
                    }
                }
            }

            Widgets.OrnateDivider {
                Layout.fillWidth: true
                ruleColor: Theme.heading
                ruleOpacity: 0.30
            }

            // ---- Empty state -----------------------------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 150
                Layout.topMargin: 4
                visible: !section._hasEquipment
                spacing: 4

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 80
                    Label {
                        anchors.centerIn: parent
                        text: "雑"
                        font.family: Theme.fontKanji
                        font.pixelSize: 110
                        color: Theme.heading
                        opacity: 0.14
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Your pack is empty.")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsHeading1
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 1.4
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                }
                Label {
                    Layout.fillWidth: true
                    Layout.maximumWidth: 460
                    Layout.alignment: Qt.AlignHCenter
                    text: qsTr("Note down the everyday effects your samurai carries — travelling clothes, a bedroll, a writing kit, whatever the journey calls for.")
                    font.italic: true
                    font.pixelSize: Theme.fsBody
                    color: Theme.ink
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    opacity: 0.7
                }
            }

            // ---- The gear list ---------------------------------------
            Repeater {
                model: section._equipment
                delegate: EquipmentRow {
                    Layout.fillWidth: true
                    item: modelData
                }
            }

            // ---- Coin purse ------------------------------------------
            Widgets.OrnateDivider {
                Layout.fillWidth: true
                Layout.topMargin: 8
                ruleColor: Theme.heading
                ruleOpacity: 0.30
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 2
                spacing: Theme.s5

                Label {
                    text: qsTr("the coin you carry")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.6
                    Layout.alignment: Qt.AlignVCenter
                }
                Item {
                    Layout.fillWidth: true
                }
                CoinField {
                    label: qsTr("Koku")
                    value: section._money.koku
                    onCommitted: function (v) {
                        if (appCtrl)
                            appCtrl.setMoney(v, section._money.bu, section._money.zeni);
                    }
                }
                CoinField {
                    label: qsTr("Bu")
                    value: section._money.bu
                    onCommitted: function (v) {
                        if (appCtrl)
                            appCtrl.setMoney(section._money.koku, v, section._money.zeni);
                    }
                }
                CoinField {
                    label: qsTr("Zeni")
                    value: section._money.zeni
                    onCommitted: function (v) {
                        if (appCtrl)
                            appCtrl.setMoney(section._money.koku, section._money.bu, v);
                    }
                }
            }
        }
    }

    // =================================================================
    // Register two -- THE EDGES (custom modifiers).
    // =================================================================
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Modifiers")

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            // ---- Header row ------------------------------------------
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: -4
                spacing: Theme.s2

                Label {
                    text: qsTr("bonuses and penalties you bring to your rolls")
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.6
                }
                Item {
                    Layout.fillWidth: true
                }
                Label {
                    visible: section._hasModifiers
                    text: section._modifiers.length === 1 ? qsTr("1 modifier") : qsTr("%1 modifiers").arg(section._modifiers.length)
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.ink
                    opacity: 0.55
                }
                AddAffordance {
                    text: qsTr("＋  Add Modifier")
                    onTriggered: modifierDlg.presentAdd()
                }
            }

            Widgets.OrnateDivider {
                Layout.fillWidth: true
                ruleColor: Theme.heading
                ruleOpacity: 0.30
            }

            // ---- Empty state -----------------------------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 150
                Layout.topMargin: 4
                visible: !section._hasModifiers
                spacing: 4

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 80
                    Label {
                        anchors.centerIn: parent
                        text: "勢"
                        font.family: Theme.fontKanji
                        font.pixelSize: 110
                        color: Theme.accent
                        opacity: 0.14
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("No modifiers set.")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsHeading1
                    font.weight: Theme.headingWeight
                    font.letterSpacing: 1.4
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.heading
                }
                Label {
                    Layout.fillWidth: true
                    Layout.maximumWidth: 460
                    Layout.alignment: Qt.AlignHCenter
                    text: qsTr("Record any standing bonus or penalty the rules don't track for you — an edge from a technique, a situational advantage, a house rule.")
                    font.italic: true
                    font.pixelSize: Theme.fsBody
                    color: Theme.ink
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    opacity: 0.7
                }
            }

            // ---- The modifier cards ----------------------------------
            Repeater {
                model: section._modifiers
                delegate: ModifierCard {
                    Layout.fillWidth: true
                    item: modelData
                }
            }
        }
    }

    // =================================================================
    // AddAffordance -- the gold-outlined ink-on-paper button shared by
    // the two registers' add actions (same vocabulary as Weapons/Skills).
    // =================================================================
    component AddAffordance: Button {
        id: addBtn
        signal triggered
        onClicked: addBtn.triggered()
        topPadding: 5
        bottomPadding: 5
        leftPadding: 14
        rightPadding: 14

        contentItem: Label {
            text: addBtn.text
            font.family: Theme.fontDisplay
            font.pixelSize: Theme.fsBody
            font.weight: Theme.wSemiBold
            font.letterSpacing: 1.6
            color: Theme.heading
            opacity: addBtn.hovered ? 1.0 : 0.88
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            color: addBtn.down ? Qt.rgba(Theme.heading.r, Theme.heading.g, Theme.heading.b, 0.18) : addBtn.hovered ? Qt.rgba(Theme.heading.r, Theme.heading.g, Theme.heading.b, 0.10) : "transparent"
            border.width: 1
            border.color: Theme.heading
            radius: 1
        }
    }

    // =================================================================
    // CoinField -- a captioned numeric field for one coin denomination.
    // Reflects external changes (a file load) imperatively rather than by
    // binding `text`, so the user's binding-break on first edit doesn't
    // strand the field; commits on editing-finished via `committed(v)`.
    // =================================================================
    component CoinField: ColumnLayout {
        id: coinField
        property string label: ""
        property int value: 0
        signal committed(int v)
        spacing: 2

        // Push external value changes back into the field's text.
        onValueChanged: coinInput.text = coinField.value

        Label {
            Layout.alignment: Qt.AlignHCenter
            text: coinField.label.toUpperCase()
            font.family: Theme.fontDisplay
            font.pixelSize: 9
            font.weight: Theme.wSemiBold
            font.letterSpacing: 1.4
            color: Theme.inkMuted
        }
        TextField {
            id: coinInput
            Layout.preferredWidth: 76
            implicitHeight: 32
            horizontalAlignment: Text.AlignHCenter
            inputMethodHints: Qt.ImhDigitsOnly
            validator: IntValidator {
                bottom: 0
                top: 999999
            }
            color: Theme.ink
            font.family: Theme.fontStat
            font.pixelSize: Theme.fsStatSmall
            font.features: Theme.tabularNumbers
            background: Rectangle {
                color: Theme.parchmentBase
                border.color: coinInput.activeFocus ? Theme.heading : Theme.borderSubtle
                border.width: 1
                radius: 2
            }
            onEditingFinished: coinField.committed(parseInt(coinInput.text || "0", 10) || 0)
            Component.onCompleted: coinInput.text = coinField.value
        }
    }

    // =================================================================
    // EquipmentRow -- one carried item. The text is editable inline; the
    // row commits on editing-finished. School-granted starting outfit
    // wears a small seal; either kind can be edited or removed (faithful
    // to the legacy list, which let you delete school items too).
    // =================================================================
    component EquipmentRow: Rectangle {
        id: row
        property var item: null
        readonly property bool _isStarting: !!(item && item.isStarting)

        implicitHeight: 38
        color: rowHover.hovered ? Theme.parchmentBase : Theme.parchmentInset
        border.color: rowHover.hovered ? Qt.darker(Theme.heading, 1.2) : Theme.borderSubtle
        border.width: 1
        radius: 2

        Behavior on color {
            ColorAnimation {
                duration: 120
            }
        }
        Behavior on border.color {
            ColorAnimation {
                duration: 120
            }
        }

        // Left rail -- gold for school-granted, muted ink for the
        // player's own additions.
        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 3
            color: row._isStarting ? Theme.heading : Theme.inkFaint
            opacity: row._isStarting ? 0.9 : 0.55
        }

        HoverHandler {
            id: rowHover
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 8
            spacing: Theme.s2

            // School seal pill.
            Rectangle {
                visible: row._isStarting
                Layout.preferredHeight: 18
                Layout.alignment: Qt.AlignVCenter
                implicitWidth: schoolLabel.implicitWidth + 14
                color: "transparent"
                border.color: Theme.heading
                border.width: 1
                radius: 9
                opacity: 0.8
                Label {
                    id: schoolLabel
                    anchors.centerIn: parent
                    text: qsTr("SCHOOL")
                    font.family: Theme.fontDisplay
                    font.pixelSize: 9
                    font.weight: Theme.wSemiBold
                    font.letterSpacing: 1.2
                    color: Theme.heading
                }
            }

            // Inline-editable text. Bound straight to the row's text;
            // the proxy rebuilds the Repeater on commit, so the binding
            // re-asserts the canonical value afterwards.
            TextField {
                id: itemInput
                Layout.fillWidth: true
                implicitHeight: 28
                text: (row.item && row.item.text) ? row.item.text : ""
                color: Theme.ink
                placeholderTextColor: Theme.inkFaint
                placeholderText: qsTr("name this item…")
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsBody
                background: Rectangle {
                    color: "transparent"
                    border.color: itemInput.activeFocus ? Theme.heading : "transparent"
                    border.width: 1
                    radius: 2
                }
                onEditingFinished: section._commitEquipment(row.item, itemInput.text)
            }

            // Remove handle -- hover-revealed crimson cross.
            Item {
                Layout.preferredWidth: 22
                Layout.preferredHeight: 22
                Layout.alignment: Qt.AlignVCenter
                AbstractButton {
                    id: equipRemoveBtn
                    anchors.fill: parent
                    visible: rowHover.hovered || equipRemoveBtn.hovered
                    onClicked: section._removeEquipment(row.item)
                    background: Rectangle {
                        radius: 11
                        color: equipRemoveBtn.hovered ? Theme.accent : "transparent"
                        border.color: Theme.accent
                        border.width: 1
                        opacity: equipRemoveBtn.hovered ? 1.0 : 0.55
                        Behavior on opacity {
                            NumberAnimation {
                                duration: 120
                            }
                        }
                    }
                    contentItem: Label {
                        text: "✕"
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: equipRemoveBtn.hovered ? Theme.whiteWash : Theme.accent
                    }
                    ToolTip.visible: hovered
                    ToolTip.delay: 400
                    ToolTip.text: qsTr("Discard this item")
                }
            }
        }
    }

    // =================================================================
    // ModifierCard -- one custom modifier. Leads with the player's reason
    // (the human note), with what-it-modifies + detail as a small-caps
    // subtitle, the value in gold on the right, an "applied" switch, and
    // hover-revealed edit / remove handles. An unapplied modifier reads
    // greyed so the live edges stand out.
    // =================================================================
    component ModifierCard: Rectangle {
        id: card
        property var item: null

        readonly property bool _active: !!(item && item.active)
        readonly property string _reason: (item && item.reason) ? item.reason : qsTr("(unnamed modifier)")
        readonly property string _typeLabel: item ? section._typeLabel(item.type) : ""
        readonly property string _detail: (item && item.detail) ? item.detail : ""
        readonly property bool _hasDetail: card._detail.length > 0
        readonly property string _value: (item && item.value) ? item.value : ""

        implicitHeight: cardBody.implicitHeight + 18
        color: cardHover.hovered ? Theme.parchmentBase : Theme.parchmentInset
        border.color: cardHover.hovered ? Qt.darker(Theme.accent, 1.2) : Theme.borderSubtle
        border.width: 1
        radius: 2

        Behavior on color {
            ColorAnimation {
                duration: 120
            }
        }
        Behavior on border.color {
            ColorAnimation {
                duration: 120
            }
        }

        // Left rail -- crimson when applied, muted ink when dormant.
        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 3
            color: card._active ? Theme.accent : Theme.inkFaint
            opacity: card._active ? 0.9 : 0.5
        }

        HoverHandler {
            id: cardHover
        }

        RowLayout {
            id: cardBody
            anchors.fill: parent
            anchors.margins: 9
            anchors.leftMargin: 13
            spacing: Theme.s4

            // ---- Reason + what-it-modifies subtitle ------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                spacing: 2
                opacity: card._active ? 1.0 : 0.55

                Label {
                    Layout.fillWidth: true
                    text: card._reason
                    font.pixelSize: Theme.fsBody + 1
                    font.weight: Theme.wRegular
                    color: Theme.ink
                    wrapMode: Text.WordWrap
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Label {
                        text: card._typeLabel.toUpperCase()
                        visible: text.length > 0
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsCaption
                        font.weight: Theme.wSemiBold
                        font.letterSpacing: 1.4
                        color: Theme.accent
                        opacity: 0.9
                    }
                    Label {
                        visible: card._hasDetail
                        text: "· " + card._detail
                        font.family: Theme.fontBody
                        font.pixelSize: Theme.fsCaption
                        color: Theme.inkMuted
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                    Item {
                        visible: !card._hasDetail
                        Layout.fillWidth: true
                    }
                }
            }

            // ---- Value ----------------------------------------------
            ColumnLayout {
                Layout.alignment: Qt.AlignVCenter
                spacing: 0
                visible: card._value.length > 0
                Label {
                    Layout.alignment: Qt.AlignRight
                    text: qsTr("VALUE")
                    font.family: Theme.fontDisplay
                    font.pixelSize: 9
                    font.weight: Theme.wSemiBold
                    font.letterSpacing: 1.2
                    color: Theme.inkMuted
                }
                Label {
                    Layout.alignment: Qt.AlignRight
                    text: card._value
                    font.family: Theme.fontStat
                    font.pixelSize: Theme.fsStatSmall
                    font.weight: Theme.wRegular
                    font.features: Theme.tabularNumbers
                    color: card._active ? Theme.heading : Theme.inkFaint
                }
            }

            // ---- Applied switch -------------------------------------
            ColumnLayout {
                Layout.alignment: Qt.AlignVCenter
                spacing: 2
                Label {
                    Layout.alignment: Qt.AlignHCenter
                    text: qsTr("APPLIED")
                    font.family: Theme.fontDisplay
                    font.pixelSize: 9
                    font.weight: Theme.wSemiBold
                    font.letterSpacing: 1.2
                    color: Theme.inkMuted
                }
                Widgets.L5RToggle {
                    Layout.alignment: Qt.AlignHCenter
                    checked: card._active
                    onToggled: {
                        if (card.item && appCtrl)
                            appCtrl.setModifierActive(card.item.id, checked);
                    }
                }
            }

            // ---- Edit handle ----------------------------------------
            Item {
                Layout.preferredWidth: 22
                Layout.preferredHeight: 22
                Layout.alignment: Qt.AlignVCenter
                AbstractButton {
                    id: modEditBtn
                    anchors.fill: parent
                    visible: cardHover.hovered || modEditBtn.hovered
                    onClicked: {
                        if (card.item)
                            modifierDlg.presentEdit(card.item);
                    }
                    background: Rectangle {
                        radius: 11
                        color: modEditBtn.hovered ? Theme.heading : "transparent"
                        border.color: Theme.heading
                        border.width: 1
                        opacity: modEditBtn.hovered ? 1.0 : 0.55
                        Behavior on opacity {
                            NumberAnimation {
                                duration: 120
                            }
                        }
                    }
                    contentItem: Label {
                        text: "✎"
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: modEditBtn.hovered ? Theme.whiteWash : Theme.heading
                    }
                    ToolTip.visible: hovered
                    ToolTip.delay: 400
                    ToolTip.text: qsTr("Edit this modifier")
                }
            }

            // ---- Remove handle --------------------------------------
            Item {
                Layout.preferredWidth: 22
                Layout.preferredHeight: 22
                Layout.alignment: Qt.AlignVCenter
                AbstractButton {
                    id: modRemoveBtn
                    anchors.fill: parent
                    visible: cardHover.hovered || modRemoveBtn.hovered
                    onClicked: section._removeModifier(card.item)
                    background: Rectangle {
                        radius: 11
                        color: modRemoveBtn.hovered ? Theme.accent : "transparent"
                        border.color: Theme.accent
                        border.width: 1
                        opacity: modRemoveBtn.hovered ? 1.0 : 0.55
                        Behavior on opacity {
                            NumberAnimation {
                                duration: 120
                            }
                        }
                    }
                    contentItem: Label {
                        text: "✕"
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: modRemoveBtn.hovered ? Theme.whiteWash : Theme.accent
                    }
                    ToolTip.visible: hovered
                    ToolTip.delay: 400
                    ToolTip.text: qsTr("Remove this modifier")
                }
            }
        }
    }
}
