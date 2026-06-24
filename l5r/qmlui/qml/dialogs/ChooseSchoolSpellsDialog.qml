// Copyright (C) 2014-2026 Daniele Simonetti
// ChooseSchoolSpellsDialog -- QML-native picker for the FREE spells a
// shugenja school grants on joining a school or advancing rank (the
// datapack's <PlayerChoose> spells copied onto the rank advancement as
// rank_.spells_to_choose, plus the rank's gained_spells_count of free
// picks). Replaces the legacy "bounded" SpellAdvDialog wizard
// (l5r/dialogs/spelldlg.py) without reusing it; opened from the Spells
// section's §6.16 callout:
//     chooseSchoolSpellsDlg.present()
//
// The legacy was a step-by-step Next/Back wizard, one spell per page. This
// re-imagines it as TABS: every granted spell is a slot the player can fill
// in any order. The active tab drives a two-pane catalogue below -- the left
// list is that slot's legal, learnable, not-yet-known spells (already
// filtered server-side by element / Maho / tag), the right pane the chosen
// spell's detail. A spell picked in one slot is hidden from the others, so no
// spell is chosen twice. On accept every slot's pick is committed at once.
//
// Slot feed shape (from appCtrl.schoolSpellChoices()):
//   { slots: [ { index, elementLabel, excludeLabel, maho, noDefic, tag,
//                options: [ catalogue record, ... ] }, ... ] }
// where each catalogue record matches availableSpellsToBuy()/BuySpellDialog:
//   { id, name, element, elementLabel, mastery, masteryMod, range, area,
//     duration, raises, tags, source, description, reach, eligible }
// On accept the dialog calls appCtrl.applySchoolSpellChoices([id, id, ...]).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: dlg

    // --- state ----------------------------------------------------
    property var _slots: []             // appCtrl.schoolSpellChoices().slots
    property var _picks: []             // spell id per slot ("" == empty)
    property int _activeSlot: 0
    property string _search: ""
    property string _elementFilter: ""  // "" == every element

    readonly property color _accent: Theme.secondary
    readonly property color _accentSoft: Qt.lighter(Theme.secondary, 1.7)
    readonly property var _activeSlotData: (_activeSlot >= 0 && _activeSlot < _slots.length) ? _slots[_activeSlot] : null

    // The element-filter options (mirrors BuySpellDialog). Most useful on an
    // unrestricted slot; on a single-element slot it is simply a no-op.
    readonly property var _elementOptions: [
        { key: "",      label: qsTr("All Elements") },
        { key: "earth", label: qsTr("Earth") },
        { key: "air",   label: qsTr("Air") },
        { key: "water", label: qsTr("Water") },
        { key: "fire",  label: qsTr("Fire") },
        { key: "void",  label: qsTr("Void") },
        { key: "multi", label: qsTr("Multi-Element") },
        { key: "dragon", label: qsTr("Dragon") }
    ]

    // --- size: kakemono proportions, capped to the overlay --------
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 80 : 900, 900)
    height: Math.min(Overlay.overlay ? Overlay.overlay.height - 80 : 680, 680)

    // --- chrome (via L5RDialog) -----------------------------------
    seal: "呪"
    accent: _accent
    accentDark: Theme.secondaryDark
    title: qsTr("Choose School Spells")
    tagline: qsTr("your school grants these prayers — fill each in any order")
    acceptText: qsTr("Inscribe")
    acceptGlyph: "呪"
    acceptEnabled: dlg._ready()
    statusText: dlg._statusHint()
    onAccepted: if (appCtrl)
        appCtrl.applySchoolSpellChoices(dlg._picks)

    // --- entrypoint -----------------------------------------------
    function present() {
        var info = (appCtrl && appCtrl.schoolSpellChoices) ? (appCtrl.schoolSpellChoices() || {}) : {};
        dlg._slots = info.slots || [];
        var p = [];
        for (var i = 0; i < dlg._slots.length; ++i)
            p.push("");
        dlg._picks = p;
        dlg._activeSlot = 0;
        dlg._search = "";
        dlg._elementFilter = "";
        elementCombo.currentIndex = 0;
        dlg.open();
    }

    // Ring hue for a spell's element, gold for multi/dragon (BuySpellDialog).
    function _ringColorFor(key) {
        if (key === "earth" || key === "air" || key === "water" || key === "fire" || key === "void")
            return Theme.ringColor(key);
        return Theme.heading;
    }

    function _pickAt(i) {
        return (i >= 0 && i < dlg._picks.length) ? (dlg._picks[i] || "") : "";
    }

    // Assign a spell to the active slot. We deliberately do NOT auto-advance
    // to the next empty slot (issue #403): the player stays on this slot so
    // they can read the spell's description, and moves on by clicking another
    // tab when ready. "Inscribe" stays disabled until every slot is filled.
    function _setActivePick(spellId) {
        var copy = dlg._picks.slice();
        copy[dlg._activeSlot] = spellId;
        dlg._picks = copy;
    }

    // The active slot's options, minus spells already taken by OTHER slots,
    // minus the element / name filters.
    function _filteredOptions() {
        if (!dlg._activeSlotData)
            return [];
        var taken = {};
        for (var i = 0; i < dlg._picks.length; ++i) {
            if (i !== dlg._activeSlot && dlg._picks[i])
                taken[dlg._picks[i]] = true;
        }
        var needle = (dlg._search || "").toLowerCase();
        var elem = dlg._elementFilter;
        var opts = dlg._activeSlotData.options || [];
        var out = [];
        for (var j = 0; j < opts.length; ++j) {
            var c = opts[j];
            if (taken[c.id])
                continue;
            if (elem.length > 0 && c.element !== elem)
                continue;
            if (needle.length > 0 && (!c.name || c.name.toLowerCase().indexOf(needle) < 0))
                continue;
            out.push(c);
        }
        return out;
    }

    // The full record for the active slot's current pick (looked up in the
    // unfiltered option list so it shows even when filtered out of the list).
    function _activeRecord() {
        var id = dlg._pickAt(dlg._activeSlot);
        if (!id || !dlg._activeSlotData)
            return null;
        var opts = dlg._activeSlotData.options || [];
        for (var i = 0; i < opts.length; ++i)
            if (opts[i].id === id)
                return opts[i];
        return null;
    }

    // Short restriction token for a slot's tab (the ring name, or a quiet
    // ANY / MAHO). Full wording lives in _slotRestrictionText.
    function _slotShortLabel(s) {
        if (!s)
            return "";
        if (s.elementLabel && s.elementLabel.length > 0)
            return s.elementLabel.toUpperCase();
        if (s.maho)
            return qsTr("MAHO");
        if (s.tag && s.tag.length > 0)
            return s.tag.toUpperCase();
        return qsTr("ANY");
    }

    // The slot restriction in full prose, for the pane header.
    function _slotRestrictionText(s) {
        if (!s)
            return "";
        var base;
        if (s.elementLabel && s.elementLabel.length > 0)
            base = qsTr("a %1 spell").arg(s.elementLabel);
        else if (s.excludeLabel && s.excludeLabel.length > 0)
            base = qsTr("any spell but %1").arg(s.excludeLabel);
        else if (s.tag && s.tag.length > 0)
            base = qsTr("a %1 spell").arg(s.tag);
        else
            base = qsTr("any spell");
        if (s.maho)
            base += qsTr(", Maho only");
        if (s.noDefic)
            base += qsTr(", deficiency set aside");
        return base;
    }

    function _filledCount() {
        var n = 0;
        for (var i = 0; i < dlg._picks.length; ++i)
            if (dlg._picks[i])
                n++;
        return n;
    }

    function _ready() {
        if (dlg._slots.length === 0)
            return false;
        return dlg._filledCount() === dlg._slots.length;
    }

    function _statusHint() {
        if (dlg._slots.length === 0)
            return qsTr("There are no spells left to choose.");
        var remaining = dlg._slots.length - dlg._filledCount();
        if (remaining > 0)
            return qsTr("Choose %n more spell(s) to continue.", "", remaining);
        return qsTr("Your prayers are chosen — inscribe them into your library.");
    }

    padding: Theme.s1   // thin inset so the opaque body reveals the gold frame

    contentItem: ColumnLayout {
        spacing: 0

        // =============================================================
        // SLOT TABS -- one tab per granted spell. Active = filled accent;
        // a filled-but-inactive slot keeps a soft wash + ✓; an empty one is
        // outlined. The row wraps if a school grants many spells.
        // =============================================================
        Rectangle {
            Layout.fillWidth: true
            color: Theme.parchmentInset
            implicitHeight: tabFlow.implicitHeight + 16
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Theme.heading
                opacity: 0.3
            }
            Flow {
                id: tabFlow
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: Theme.s2

                Repeater {
                    model: dlg._slots
                    delegate: AbstractButton {
                        id: tab
                        required property int index
                        required property var modelData
                        readonly property bool _on: dlg._activeSlot === index
                        readonly property string _pick: dlg._pickAt(index)
                        readonly property bool _filled: _pick.length > 0
                        readonly property string _pickName: {
                            var opts = modelData.options || [];
                            for (var i = 0; i < opts.length; ++i)
                                if (opts[i].id === tab._pick)
                                    return opts[i].name || "";
                            return "";
                        }

                        // Roomy inset so the restriction + chosen-spell lines
                        // breathe (the size derives from the content + these
                        // paddings rather than a fixed height/width hack).
                        leftPadding: Theme.s4
                        rightPadding: Theme.s4
                        topPadding: Theme.s3
                        bottomPadding: Theme.s3
                        implicitHeight: tabRow.implicitHeight + topPadding + bottomPadding
                        implicitWidth: Math.max(124, tabRow.implicitWidth + leftPadding + rightPadding)
                        onClicked: dlg._activeSlot = index

                        background: Rectangle {
                            radius: 3
                            color: tab._on ? dlg._accent : (tab._filled ? Theme.secondarySoft : (tab.hovered ? Qt.rgba(dlg._accent.r, dlg._accent.g, dlg._accent.b, 0.08) : "transparent"))
                            border.color: dlg._accent
                            border.width: tab._on ? 0 : 1
                            Behavior on color {
                                ColorAnimation {
                                    duration: Theme.durHover
                                }
                            }
                        }

                        contentItem: RowLayout {
                            id: tabRow
                            spacing: 8
                            ColumnLayout {
                                id: tabCol
                                Layout.fillWidth: true
                                spacing: 1
                                Label {
                                    text: dlg._slotShortLabel(tab.modelData)
                                    font.family: Theme.fontDisplay
                                    font.pixelSize: Theme.fsCaption
                                    font.weight: Theme.wSemiBold
                                    font.letterSpacing: 1.2
                                    color: tab._on ? Theme.whiteWash : dlg._accent
                                }
                                Label {
                                    Layout.maximumWidth: 150
                                    text: tab._filled ? tab._pickName : qsTr("choose…")
                                    font.family: Theme.fontBody
                                    font.italic: !tab._filled
                                    font.pixelSize: Theme.fsCaption
                                    color: tab._on ? Theme.whiteWash : (tab._filled ? Theme.ink : Theme.inkMuted)
                                    elide: Text.ElideRight
                                }
                            }
                            Label {
                                visible: tab._filled
                                text: "✓"
                                font.pixelSize: Theme.fsBody
                                font.weight: Theme.wSemiBold
                                color: tab._on ? Theme.whiteWash : Theme.positive
                            }
                        }
                    }
                }
            }
        }

        // =============================================================
        // FILTER BAND -- element dropdown + search, scoping the active slot.
        // =============================================================
        Rectangle {
            Layout.fillWidth: true
            color: Theme.parchmentSidebar
            implicitHeight: filterRow.implicitHeight + 14
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Theme.borderSubtle
            }
            RowLayout {
                id: filterRow
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 12

                // The slot's restriction, spelled out for the player.
                Label {
                    Layout.fillWidth: true
                    text: dlg._activeSlotData ? qsTr("This slot wants %1.").arg(dlg._slotRestrictionText(dlg._activeSlotData)) : ""
                    font.family: Theme.fontBody
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.inkMuted
                    elide: Text.ElideRight
                }

                Widgets.L5RComboBox {
                    id: elementCombo
                    Layout.preferredWidth: 150
                    textRole: "label"
                    model: dlg._elementOptions
                    accent: dlg._accent
                    onActivated: function (index) {
                        var opt = dlg._elementOptions[index];
                        dlg._elementFilter = opt ? opt.key : "";
                    }
                }

                Widgets.L5RSearchField {
                    Layout.preferredWidth: 200
                    placeholder: qsTr("seek a spell by name…")
                    onTextChanged: dlg._search = text
                }
            }
        }

        // =============================================================
        // BODY -- catalogue list | divider | detail pane.
        // =============================================================
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // ---- LEFT: the active slot's catalogue --------------------
            Pane {
                Layout.fillHeight: true
                Layout.preferredWidth: 320
                padding: 0
                background: Rectangle {
                    color: Theme.parchmentSidebar
                    radius: 0
                    Widgets.RicePaperOverlay {}
                }
                palette.windowText: Theme.ink
                palette.text: Theme.ink
                palette.base: Theme.parchmentBase

                ListView {
                    id: catalogView
                    anchors.fill: parent
                    clip: true
                    model: dlg._filteredOptions()
                    spacing: 0
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }

                    delegate: AbstractButton {
                        id: row
                        width: catalogView.width
                        implicitHeight: 46
                        required property var modelData
                        readonly property bool _active: dlg._pickAt(dlg._activeSlot) === modelData.id
                        readonly property color _ringColor: dlg._ringColorFor(modelData.element || "void")

                        onClicked: dlg._setActivePick(modelData.id)

                        background: Rectangle {
                            color: row._active ? dlg._accentSoft : (row.hovered ? Qt.lighter(Theme.parchmentSidebar, 1.04) : "transparent")
                            Rectangle {
                                anchors.left: parent.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: row._active ? 3 : 0
                                color: dlg._accent
                            }
                        }

                        contentItem: RowLayout {
                            anchors.fill: parent
                            spacing: 8

                            Rectangle {
                                Layout.leftMargin: row._active ? 13 : 11
                                Layout.alignment: Qt.AlignVCenter
                                implicitWidth: 8
                                implicitHeight: 8
                                radius: 4
                                color: row._ringColor
                            }
                            Label {
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignVCenter
                                verticalAlignment: Text.AlignVCenter
                                text: modelData.name || qsTr("(unnamed)")
                                font.pixelSize: Theme.fsBody
                                font.weight: row._active ? Theme.wSemiBold : Theme.wRegular
                                color: Theme.ink
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.rightMargin: 12
                                Layout.alignment: Qt.AlignVCenter
                                text: qsTr("M%1").arg(modelData.mastery || 0)
                                font.family: Theme.fontStat
                                font.pixelSize: Theme.fsStatSmall
                                font.features: Theme.tabularNumbers
                                color: row._ringColor
                                opacity: 0.95
                            }
                        }
                    }

                    Label {
                        anchors.centerIn: parent
                        width: parent.width - 32
                        visible: catalogView.count === 0
                        horizontalAlignment: Text.AlignHCenter
                        text: qsTr("no spell answers this slot's calling")
                        font.italic: true
                        font.pixelSize: Theme.fsCaption
                        color: Theme.ink
                        opacity: 0.55
                        wrapMode: Text.WordWrap
                    }
                }
            }

            // ---- vertical divider -------------------------------------
            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: Theme.heading
                opacity: 0.35
            }

            // ---- RIGHT: the active slot's chosen-spell detail ---------
            Pane {
                id: detailPane
                Layout.fillWidth: true
                Layout.fillHeight: true
                padding: 0
                background: Rectangle {
                    color: Theme.parchment
                    radius: 0
                    Widgets.RicePaperOverlay {}
                }
                palette.windowText: Theme.ink
                palette.text: Theme.ink
                palette.base: Theme.parchmentBase
                palette.alternateBase: Theme.parchmentInset
                palette.placeholderText: Theme.inkFaint
                palette.buttonText: Theme.ink

                readonly property var _rec: dlg._activeRecord()
                readonly property color _ringColor: _rec ? dlg._ringColorFor(_rec.element || "void") : dlg._accent

                // ---- Unselected state ----------------------------------
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 24
                    visible: detailPane._rec === null
                    spacing: 4

                    Item {
                        Layout.fillHeight: true
                    }
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: "呪"
                        font.family: Theme.fontKanji
                        font.pixelSize: 130
                        color: dlg._accent
                        opacity: 0.13
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Choose a spell for this slot from the register at your left.")
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsHeading1
                        font.weight: Theme.headingWeight
                        font.letterSpacing: 1.4
                        horizontalAlignment: Text.AlignHCenter
                        color: Theme.heading
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        Layout.fillWidth: true
                        Layout.maximumWidth: 380
                        Layout.alignment: Qt.AlignHCenter
                        text: qsTr("Every spell shown lies within your reach. Switch slots with the tabs above and fill them in whatever order you please.")
                        font.italic: true
                        font.pixelSize: Theme.fsBody
                        color: Theme.ink
                        horizontalAlignment: Text.AlignHCenter
                        opacity: 0.7
                        wrapMode: Text.WordWrap
                    }
                    Item {
                        Layout.fillHeight: true
                    }
                }

                // ---- Selected state ------------------------------------
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 22
                    visible: detailPane._rec !== null
                    spacing: 10

                    Label {
                        Layout.fillWidth: true
                        text: detailPane._rec ? detailPane._rec.name : ""
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsDisplay
                        font.weight: Theme.headingWeight
                        font.letterSpacing: 1.0
                        color: Theme.heading
                        wrapMode: Text.WordWrap
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: detailPane._ringColor
                        opacity: 0.5
                    }

                    // Meta row -- element chip + mastery pill + affinity chip.
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        readonly property int _mod: detailPane._rec ? (detailPane._rec.masteryMod || 0) : 0

                        Rectangle {
                            Layout.preferredHeight: 20
                            implicitWidth: elementLabel.implicitWidth + 18
                            radius: 10
                            color: detailPane._ringColor
                            Label {
                                id: elementLabel
                                anchors.centerIn: parent
                                text: detailPane._rec ? (detailPane._rec.elementLabel || "").toUpperCase() : ""
                                font.family: Theme.fontDisplay
                                font.pixelSize: Theme.fsMicro
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.4
                                color: Theme.whiteWash
                            }
                        }
                        Rectangle {
                            Layout.preferredHeight: 20
                            implicitWidth: masteryLabel.implicitWidth + 18
                            color: "transparent"
                            border.color: detailPane._ringColor
                            border.width: 1
                            radius: 10
                            opacity: 0.85
                            Label {
                                id: masteryLabel
                                anchors.centerIn: parent
                                text: qsTr("Mastery %1").arg(detailPane._rec ? (detailPane._rec.mastery || 0) : 0)
                                font.family: Theme.fontDisplay
                                font.pixelSize: Theme.fsMicro
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.2
                                color: detailPane._ringColor
                            }
                        }
                        Rectangle {
                            visible: parent._mod !== 0
                            Layout.preferredHeight: 20
                            implicitWidth: modLabel.implicitWidth + 16
                            radius: 10
                            color: "transparent"
                            border.width: 1
                            border.color: parent._mod > 0 ? Theme.positive : Theme.accent
                            opacity: 0.9
                            Label {
                                id: modLabel
                                anchors.centerIn: parent
                                text: parent.parent._mod > 0 ? qsTr("AFFINITY +%1").arg(parent.parent._mod) : qsTr("DEFICIENCY %1").arg(parent.parent._mod)
                                font.family: Theme.fontDisplay
                                font.pixelSize: Theme.fsMicro
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.2
                                color: parent.parent._mod > 0 ? Theme.positive : Theme.accent
                            }
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                        Label {
                            visible: detailPane._rec && detailPane._rec.source
                            text: detailPane._rec ? detailPane._rec.source : ""
                            font.italic: true
                            font.pixelSize: Theme.fsCaption
                            color: Theme.ink
                            opacity: 0.55
                        }
                    }

                    // Casting line -- range / area / duration / raises.
                    Flow {
                        Layout.fillWidth: true
                        spacing: 18
                        Repeater {
                            model: detailPane._rec ? [
                                { k: qsTr("RANGE"), v: detailPane._rec.range || "" },
                                { k: qsTr("AREA"), v: detailPane._rec.area || "" },
                                { k: qsTr("DURATION"), v: detailPane._rec.duration || "" },
                                { k: qsTr("RAISES"), v: detailPane._rec.raises || "" }
                            ] : []
                            delegate: ColumnLayout {
                                visible: (modelData.v || "").length > 0
                                spacing: 0
                                Label {
                                    text: modelData.k
                                    font.family: Theme.fontDisplay
                                    font.pixelSize: Theme.fsMicro
                                    font.weight: Theme.wSemiBold
                                    font.letterSpacing: 1.6
                                    color: Theme.heading
                                    opacity: 0.8
                                }
                                Label {
                                    text: modelData.v
                                    font.pixelSize: Theme.fsCaption
                                    color: Theme.ink
                                    opacity: 0.85
                                }
                            }
                        }
                    }

                    // Description.
                    ScrollView {
                        id: descScroll
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        contentWidth: availableWidth
                        Label {
                            width: descScroll.availableWidth
                            text: detailPane._rec && detailPane._rec.description ? detailPane._rec.description : qsTr("No description provided in the datapack.")
                            font.pixelSize: Theme.fsBody
                            wrapMode: Text.WordWrap
                            textFormat: Text.PlainText
                            color: Theme.ink
                        }
                    }

                    // Tags footnote.
                    Flow {
                        Layout.fillWidth: true
                        visible: detailPane._rec && detailPane._rec.tags && detailPane._rec.tags.length > 0
                        spacing: 6
                        Repeater {
                            model: detailPane._rec && detailPane._rec.tags ? detailPane._rec.tags : []
                            delegate: Rectangle {
                                implicitHeight: 18
                                implicitWidth: tagLabel.implicitWidth + 14
                                radius: 9
                                color: "transparent"
                                border.width: 1
                                border.color: Theme.borderSubtle
                                Label {
                                    id: tagLabel
                                    anchors.centerIn: parent
                                    text: (modelData || "").toUpperCase()
                                    font.family: Theme.fontDisplay
                                    font.pixelSize: Theme.fsMicro
                                    font.weight: Theme.wSemiBold
                                    font.letterSpacing: 1.0
                                    color: Theme.inkMuted
                                }
                            }
                        }
                    }
                }
            }
        }   // body RowLayout
    }
}
