// Copyright (C) 2014-2026 Daniele Simonetti
// BuyKataDialog -- QML-native catalogue picker for learning a kata.
// Replaces the legacy QWidget KataDialog (l5r/dialogs/katadlg.py)
// without reusing any of its widgets. Opened from KataSection:
//     buyKataDlg.present()
// (The entrypoint is `present` rather than `open` so it does not shadow
// Dialog's built-in open(), which present() calls to pop the modal up.)
//
// A two-pane brushed scroll, kakemono-aspect (taller than wide). The
// left column is the catalogue of not-yet-known kata, each row carrying
// an element-colour dot and a mastery tag; ineligible forms are dimmed
// so the eye is drawn to what can actually be learned. The right column
// is the chosen form's detail: an element chip + mastery pill, the
// prose, then "WHAT THE FORM DEMANDS" -- the Ring it draws upon (with
// the character's current rank measured against it) and its rulebook
// requirements, each marked met or unmet. The footer plaque states the
// XP cost; the Learn button enables only when the form is eligible,
// gating exactly as the legacy KataDialog did (match at least one
// requirement AND Ring rank >= mastery).
//
// Catalogue entry shape (from appCtrl.availableKataToBuy()):
//   { id, name,
//     element:      "fire",        // ring key -> Theme.ringColor
//     elementLabel: "Fire",
//     mastery:      3,
//     cost:         3,             // XP (== mastery)
//     description:  "...",
//     source:       "Core p.182",
//     requirements: [ { text, met:bool, roleplay:bool }, ... ],
//     ringNeed:     { label:"Fire", needed:3, have:2, met:false },
//     eligible:     false }
// On accept the dialog calls appCtrl.buyKata(id).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: dlg

    // --- state ----------------------------------------------------
    property var _catalogue: []
    property var _selected: null
    property string _search: ""

    // --- derived --------------------------------------------------
    // Kata is a learned discipline -> the blue "blessing/cultivation"
    // accent family, matching BuySkillDialog. The per-kata element hue
    // is data shown in the detail pane, not the dialog's identity.
    readonly property color _accent: Theme.secondary
    readonly property color _accentSoft: Qt.lighter(Theme.secondary, 1.7)
    readonly property int _cost: _selected ? (_selected.cost || 0) : 0
    readonly property bool _eligible: !!(_selected && _selected.eligible)

    // --- size: kakemono proportions, capped to the overlay --------
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 80 : 880, 880)
    height: Math.min(Overlay.overlay ? Overlay.overlay.height - 80 : 640, 640)

    // --- chrome (via L5RDialog) -----------------------------------
    seal: "型"
    title: qsTr("Learn a Kata")
    tagline: qsTr("a form is yours only when body and spirit are ready for it")
    accent: _accent
    accentDark: Theme.secondaryDark
    acceptText: qsTr("Learn")
    acceptGlyph: "型"
    acceptEnabled: dlg._eligible
    statusText: {
        if (!dlg._selected)
            return "";
        if (dlg._eligible)
            return qsTr("This form will require %1 XP.").arg(dlg._cost);
        return dlg._reasonFor(dlg._selected);
    }
    onAccepted: {
        if (dlg._selected && dlg._eligible && appCtrl)
            appCtrl.buyKata(dlg._selected.id);
    }

    // --- entrypoint -----------------------------------------------
    function present() {
        dlg._refreshCatalogue();
        dlg._selected = null;
        dlg._search = "";
        dlg.open();
    }

    function _refreshCatalogue() {
        dlg._catalogue = (appCtrl && appCtrl.availableKataToBuy) ? (appCtrl.availableKataToBuy() || []) : [];
    }

    function _filteredCatalogue() {
        var needle = (dlg._search || "").toLowerCase();
        if (needle.length === 0)
            return dlg._catalogue;
        var out = [];
        for (var i = 0; i < dlg._catalogue.length; ++i) {
            var c = dlg._catalogue[i];
            if (c.name && c.name.toLowerCase().indexOf(needle) >= 0)
                out.push(c);
        }
        return out;
    }

    // One short sentence on why a form can't be learned -- Ring first
    // (the legacy dialog showed the ring gate most prominently), then
    // the requirements gate.
    function _reasonFor(k) {
        if (!k)
            return "";
        if (k.ringNeed && k.ringNeed.met === false)
            return qsTr("Your %1 Ring must reach %2 — you have %3.").arg(k.ringNeed.label).arg(k.ringNeed.needed).arg(k.ringNeed.have);
        return qsTr("You match none of this form's requirements.");
    }

    padding: Theme.s1   // thin inset so the opaque two-pane body reveals the gold frame

    contentItem: ColumnLayout {
        spacing: 0

        // =============================================================
        // FILTER BAND -- search field spanning both panes.
        // =============================================================
        Rectangle {
            Layout.fillWidth: true
            color: Theme.parchmentInset
            implicitHeight: filterRow.implicitHeight + 16
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: Theme.heading
                opacity: 0.3
            }
            RowLayout {
                id: filterRow
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 12

                Widgets.L5RSearchField {
                    id: searchField
                    Layout.fillWidth: true
                    placeholder: qsTr("seek a form by name…")
                    onTextChanged: dlg._search = text
                }
            }
        }

        // =============================================================
        // The body row -- catalogue list, divider, detail pane.
        // =============================================================
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // =========================================================
            // LEFT PANE -- the catalogue list.
            // =========================================================
            Pane {
                id: catalogPane
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
                    model: dlg._filteredCatalogue()
                    spacing: 0
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }

                    delegate: AbstractButton {
                        id: row
                        width: catalogView.width
                        implicitHeight: 46
                        readonly property bool _active: dlg._selected && dlg._selected.id === modelData.id
                        readonly property bool _eligible: !!modelData.eligible
                        readonly property color _ringColor: Theme.ringColor(modelData.element || "void")

                        onClicked: dlg._selected = modelData

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

                            // Element dot -- colour-codes the form's Ring.
                            Rectangle {
                                Layout.leftMargin: row._active ? 13 : 11
                                Layout.alignment: Qt.AlignVCenter
                                implicitWidth: 8
                                implicitHeight: 8
                                radius: 4
                                color: row._ringColor
                                opacity: row._eligible ? 1.0 : 0.4
                            }
                            Label {
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignVCenter
                                verticalAlignment: Text.AlignVCenter
                                text: modelData.name || qsTr("(unnamed)")
                                font.pixelSize: Theme.fsBody
                                font.weight: row._active ? Theme.wSemiBold : Theme.wRegular
                                color: Theme.ink
                                opacity: row._eligible ? 1.0 : 0.5
                                elide: Text.ElideRight
                            }
                            // Mastery tag.
                            Label {
                                Layout.rightMargin: 12
                                Layout.alignment: Qt.AlignVCenter
                                text: qsTr("M%1").arg(modelData.mastery || 0)
                                font.family: Theme.fontStat
                                font.pixelSize: Theme.fsStatSmall
                                font.features: Theme.tabularNumbers
                                color: row._ringColor
                                opacity: row._eligible ? 0.95 : 0.45
                            }
                        }
                    }

                    Label {
                        anchors.centerIn: parent
                        visible: catalogView.count === 0
                        text: dlg._catalogue.length === 0 ? qsTr("every form is already known") : qsTr("nothing matches that brushstroke")
                        font.italic: true
                        font.pixelSize: Theme.fsCaption
                        color: Theme.ink
                        opacity: 0.55
                    }
                }
            }

            // =========================================================
            // VERTICAL DIVIDER.
            // =========================================================
            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: Theme.heading
                opacity: 0.35
            }

            // =========================================================
            // RIGHT PANE -- the chosen form's detail.
            // =========================================================
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

                readonly property color _ringColor: dlg._selected ? Theme.ringColor(dlg._selected.element || "void") : Theme.accent

                // ---- Unselected state ----------------------------------
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 24
                    visible: dlg._selected === null
                    spacing: 4

                    Item {
                        Layout.fillHeight: true
                    }
                    Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: "型"
                        font.family: Theme.fontKanji
                        font.pixelSize: 130
                        color: dlg._accent
                        opacity: 0.13
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Choose a form from the register at your left.")
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
                        text: qsTr("Dimmed forms lie beyond your present mastery — deepen the Ring they draw upon, or earn their requirements first.")
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
                    visible: dlg._selected !== null
                    spacing: 10

                    // Title.
                    Label {
                        Layout.fillWidth: true
                        text: dlg._selected ? dlg._selected.name : ""
                        font.family: Theme.fontDisplay
                        font.pixelSize: 22
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

                    // Meta row -- element chip + mastery pill + source.
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        // Element chip -- filled in the Ring's hue.
                        Rectangle {
                            Layout.preferredHeight: 20
                            implicitWidth: elementLabel.implicitWidth + 18
                            radius: 10
                            color: detailPane._ringColor
                            Label {
                                id: elementLabel
                                anchors.centerIn: parent
                                text: dlg._selected ? (dlg._selected.elementLabel || "").toUpperCase() : ""
                                font.family: Theme.fontDisplay
                                font.pixelSize: 10
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.4
                                color: Theme.whiteWash
                            }
                        }
                        // Mastery pill -- outlined in the Ring's hue.
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
                                text: qsTr("Mastery %1").arg(dlg._selected ? (dlg._selected.mastery || 0) : 0)
                                font.family: Theme.fontDisplay
                                font.pixelSize: 10
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.2
                                color: detailPane._ringColor
                            }
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                        Label {
                            visible: dlg._selected && dlg._selected.source
                            text: dlg._selected ? dlg._selected.source : ""
                            font.italic: true
                            font.pixelSize: Theme.fsCaption
                            color: Theme.ink
                            opacity: 0.55
                        }
                    }

                    // Description -- scrolls if long; the demands + price
                    // stay pinned below.
                    ScrollView {
                        id: descScroll
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        contentWidth: availableWidth
                        Label {
                            width: descScroll.availableWidth
                            text: dlg._selected && dlg._selected.description ? dlg._selected.description : qsTr("No description provided in the datapack.")
                            font.pixelSize: Theme.fsBody
                            wrapMode: Text.WordWrap
                            textFormat: Text.PlainText
                            color: Theme.ink
                        }
                    }

                    // =====================================================
                    // WHAT THE FORM DEMANDS -- the Ring gate + the rulebook
                    // requirements, each marked met or unmet. This is the
                    // heart of the dialog: it shows the player exactly why
                    // a form is or isn't within reach.
                    // =====================================================
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: demandsBody.implicitHeight + 22
                        color: Theme.parchmentInset
                        border.color: dlg._eligible ? Theme.borderSubtle : Theme.accent
                        border.width: dlg._eligible ? 1 : 1.5
                        radius: 2

                        Behavior on border.color {
                            ColorAnimation {
                                duration: 160
                            }
                        }

                        ColumnLayout {
                            id: demandsBody
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            RowLayout {
                                Layout.fillWidth: true
                                Label {
                                    Layout.fillWidth: true
                                    text: qsTr("WHAT THE FORM DEMANDS")
                                    font.family: Theme.fontDisplay
                                    font.pixelSize: Theme.fsCaption
                                    font.weight: Theme.headingWeight
                                    font.letterSpacing: 2.0
                                    color: Theme.heading
                                    opacity: 0.9
                                }
                                // Compact XP plaque -- cost == mastery.
                                RowLayout {
                                    spacing: 4
                                    Label {
                                        text: dlg._cost
                                        font.family: Theme.fontStat
                                        font.pixelSize: Theme.fsXpValue
                                        font.weight: Theme.wSemiBold
                                        font.features: Theme.tabularNumbers
                                        color: dlg._accent
                                    }
                                    Label {
                                        Layout.alignment: Qt.AlignBottom
                                        Layout.bottomMargin: 5
                                        text: qsTr("XP")
                                        font.family: Theme.fontDisplay
                                        font.pixelSize: 9
                                        font.weight: Theme.headingWeight
                                        font.letterSpacing: 2.0
                                        color: dlg._accent
                                        opacity: 0.8
                                    }
                                }
                            }

                            // Ring gate line.
                            RowLayout {
                                Layout.fillWidth: true
                                visible: dlg._selected && dlg._selected.ringNeed
                                spacing: 8

                                readonly property bool _met: !!(dlg._selected && dlg._selected.ringNeed && dlg._selected.ringNeed.met)

                                Label {
                                    text: parent._met ? "✓" : "✕"
                                    font.pixelSize: Theme.fsBody
                                    color: parent._met ? Theme.positive : Theme.accent
                                    Layout.preferredWidth: 14
                                    horizontalAlignment: Text.AlignHCenter
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: dlg._selected && dlg._selected.ringNeed ? qsTr("%1 Ring of %2 — you have %3").arg(dlg._selected.ringNeed.label).arg(dlg._selected.ringNeed.needed).arg(dlg._selected.ringNeed.have) : ""
                                    font.pixelSize: Theme.fsBody
                                    color: Theme.ink
                                    opacity: parent._met ? 0.9 : 1.0
                                    wrapMode: Text.WordWrap
                                }
                            }

                            // Requirements heading -- only when there are any.
                            Label {
                                visible: dlg._selected && dlg._selected.requirements && dlg._selected.requirements.length > 0
                                text: qsTr("Match at least one:")
                                font.italic: true
                                font.pixelSize: Theme.fsCaption
                                color: Theme.ink
                                opacity: 0.6
                            }

                            // Requirement rows.
                            Repeater {
                                model: dlg._selected && dlg._selected.requirements ? dlg._selected.requirements : []
                                delegate: RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8

                                    readonly property bool _roleplay: !!modelData.roleplay
                                    readonly property bool _met: !!modelData.met

                                    Label {
                                        // Roleplay reqs are advisory (the gate
                                        // ignores them) -> a neutral diamond,
                                        // not a pass/fail mark.
                                        text: parent._roleplay ? "◇" : (parent._met ? "✓" : "✕")
                                        font.pixelSize: Theme.fsBody
                                        color: parent._roleplay ? Theme.inkMuted : (parent._met ? Theme.positive : Theme.accent)
                                        Layout.preferredWidth: 14
                                        horizontalAlignment: Text.AlignHCenter
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: parent._roleplay ? qsTr("%1  (by roleplay)").arg(modelData.text || "") : (modelData.text || "")
                                        font.pixelSize: Theme.fsBody
                                        font.italic: parent._roleplay
                                        color: Theme.ink
                                        opacity: (parent._roleplay || parent._met) ? 0.85 : 1.0
                                        wrapMode: Text.WordWrap
                                    }
                                }
                            }

                            // No-requirements note.
                            Label {
                                visible: dlg._selected && (!dlg._selected.requirements || dlg._selected.requirements.length === 0)
                                Layout.fillWidth: true
                                text: qsTr("This form sets no further requirements.")
                                font.italic: true
                                font.pixelSize: Theme.fsCaption
                                color: Theme.ink
                                opacity: 0.55
                            }
                        }
                    }
                }
            }
        }   // body RowLayout
    }
}
