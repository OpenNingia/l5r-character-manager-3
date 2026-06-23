// Copyright (C) 2014-2026 Daniele Simonetti
// BuyKihoDialog -- QML-native catalogue picker for learning a kiho.
// Replaces the legacy QWidget KihoDialog (l5r/dialogs/kihodlg.py) without
// reusing any of its widgets. Opened from KihoSection:
//     buyKihoDlg.present()
// (The entrypoint is `present` rather than `open` so it does not shadow
// Dialog's built-in open(), which present() calls to pop the modal up.)
//
// A two-pane brushed scroll, kakemono-aspect (taller than wide). The left
// column is the catalogue of not-yet-known kiho, each row carrying an
// element-colour dot and a mastery tag; kiho the character cannot yet
// learn are dimmed so the eye is drawn to what is within reach. The right
// column is the chosen kiho's detail: an element chip + mastery pill +
// type pill, the prose, then "WHAT THE KIHO DEMANDS" -- the character's
// standing on the kiho paths (Monk / Shugenja / Ninja) and, once that
// gate is met, whether their Ring or School rank runs deep enough. The
// footer plaque states the XP cost; the Learn button enables only when
// the kiho is eligible, gating exactly as the legacy KihoDialog did.
//
// Catalogue entry shape (from appCtrl.availableKihoToBuy()):
//   { id, name,
//     element:      "fire",        // ring key -> Theme.ringColor
//     elementLabel: "Fire",
//     mastery:      3,
//     type:         "martial",     // kiho kind, lower-cased key
//     typeLabel:    "Martial",
//     cost:         6,             // class-scaled XP
//     description:  "...",
//     source:       "Core p.182",
//     path:         { kind:"shugenja", met:true },  // character-wide
//     eligible:     false,
//     reason:       "Your Fire Ring Rank is not enough" }  // when path met
// On accept the dialog calls appCtrl.buyKiho(id).
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
    // Kiho is a learned discipline -> the blue "blessing/cultivation"
    // accent family, matching BuyKataDialog / BuySkillDialog. The per-kiho
    // element hue is data shown in the detail pane, not the dialog's
    // identity.
    readonly property color _accent: Theme.secondary
    readonly property color _accentSoft: Qt.lighter(Theme.secondary, 1.7)
    readonly property int _cost: _selected ? (_selected.cost || 0) : 0
    readonly property bool _eligible: !!(_selected && _selected.eligible)
    readonly property bool _pathMet: !!(_selected && _selected.path && _selected.path.met)

    // Free kiho granted by a School rank (monks): the next kiho learned
    // costs no XP, whichever it is, so an eligible kiho shows as free while
    // any remain. The discount is applied for real by
    // api.character.powers.buy_kiho; here we only reflect it honestly.
    readonly property int _freeKiho: (pcProxy && pcProxy.freeKihoCount) ? pcProxy.freeKihoCount : 0
    readonly property bool _free: _freeKiho > 0
    readonly property int _effectiveCost: _free ? 0 : _cost

    // --- size: kakemono proportions, capped to the overlay --------
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 80 : 880, 880)
    height: Math.min(Overlay.overlay ? Overlay.overlay.height - 80 : 640, 640)

    // --- chrome (via L5RDialog) -----------------------------------
    seal: "気"
    title: qsTr("Learn a Kiho")
    tagline: qsTr("the disciplines of breath and spirit, kept by the devoted")
    accent: _accent
    accentDark: Theme.secondaryDark
    acceptText: qsTr("Learn")
    acceptGlyph: "気"
    acceptEnabled: dlg._eligible
    statusText: {
        if (!dlg._selected)
            return "";
        if (dlg._eligible)
            return dlg._free ? qsTr("This kiho is granted by your rank — no experience spent.") : qsTr("This kiho will require %1 XP.").arg(dlg._cost);
        return dlg._reasonFor(dlg._selected);
    }
    onAccepted: {
        if (dlg._selected && dlg._eligible && appCtrl)
            appCtrl.buyKiho(dlg._selected.id);
    }

    // --- entrypoint -----------------------------------------------
    function present() {
        dlg._refreshCatalogue();
        dlg._selected = null;
        dlg._search = "";
        dlg.open();
    }

    function _refreshCatalogue() {
        dlg._catalogue = (appCtrl && appCtrl.availableKihoToBuy) ? (appCtrl.availableKihoToBuy() || []) : [];
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

    // The character's standing on the kiho paths -- the same for every
    // kiho (it depends on who you are, not which kiho), so it reads from
    // path.kind. Plain copy, no mechanics jargon.
    function _pathLabel(k) {
        if (!k || !k.path)
            return "";
        switch (k.path.kind) {
        case "brotherhood":
            return qsTr("You walk with the Brotherhood of Shinsei");
        case "monk":
            return qsTr("You are a Monk");
        case "ninja":
            return qsTr("You are a Ninja");
        case "shugenja":
            return qsTr("You are a Shugenja");
        default:
            return qsTr("You follow none of the paths that may learn kiho");
        }
    }

    // One short sentence on why a kiho can't be learned -- the path gate
    // first (it is the hard prerequisite), then the Ring/School reason the
    // api supplied once that gate is met.
    function _reasonFor(k) {
        if (!k)
            return "";
        if (!(k.path && k.path.met))
            return qsTr("Only Monks, Ninja, and Shugenja may learn kiho.");
        return k.reason && k.reason.length > 0 ? k.reason : qsTr("Your Ring or School rank is not yet deep enough.");
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
                    placeholder: qsTr("seek a kiho by name…")
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

                            // Element dot -- colour-codes the kiho's Ring.
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
                        text: dlg._catalogue.length === 0 ? qsTr("every kiho is already known") : qsTr("nothing matches that brushstroke")
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
            // RIGHT PANE -- the chosen kiho's detail.
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
                        text: "気"
                        font.family: Theme.fontKanji
                        font.pixelSize: 130
                        color: dlg._accent
                        opacity: 0.13
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Choose a kiho from the register at your left.")
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
                        text: qsTr("Dimmed kiho lie beyond your present discipline — walk the right path, deepen the Ring they draw upon, or rise in School rank first.")
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

                    // Meta row -- element chip + mastery pill + type pill
                    // + source.
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
                                font.pixelSize: Theme.fsMicro
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
                                font.pixelSize: Theme.fsMicro
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.2
                                color: detailPane._ringColor
                            }
                        }
                        // Type pill -- the kiho kind (Internal / Martial /
                        // Mystical), in a neutral ink so the Ring hue stays
                        // the row's identity colour.
                        Rectangle {
                            visible: dlg._selected && dlg._selected.typeLabel && dlg._selected.typeLabel.length > 0
                            Layout.preferredHeight: 20
                            implicitWidth: typeLabel.implicitWidth + 18
                            color: "transparent"
                            border.color: Theme.inkMuted
                            border.width: 1
                            radius: 10
                            opacity: 0.85
                            Label {
                                id: typeLabel
                                anchors.centerIn: parent
                                text: dlg._selected ? (dlg._selected.typeLabel || "").toUpperCase() : ""
                                font.family: Theme.fontDisplay
                                font.pixelSize: Theme.fsMicro
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.2
                                color: Theme.inkMuted
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
                    // WHAT THE KIHO DEMANDS -- the path gate + (once met)
                    // the Ring/School-rank gate, each marked met or unmet.
                    // This is the heart of the dialog: it shows the player
                    // exactly why a kiho is or isn't within reach.
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
                                    text: qsTr("WHAT THE KIHO DEMANDS")
                                    font.family: Theme.fontDisplay
                                    font.pixelSize: Theme.fsCaption
                                    font.weight: Theme.headingWeight
                                    font.letterSpacing: 2.0
                                    color: Theme.heading
                                    opacity: 0.9
                                }
                                // Compact XP plaque -- class-scaled cost,
                                // shown as 0 when a rank-granted free kiho
                                // will cover it.
                                RowLayout {
                                    spacing: 4
                                    Label {
                                        text: dlg._effectiveCost
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
                                        font.pixelSize: Theme.fsMicro
                                        font.weight: Theme.headingWeight
                                        font.letterSpacing: 2.0
                                        color: dlg._accent
                                        opacity: 0.8
                                    }
                                }
                            }

                            // Free-kiho note -- explains the 0 XP plaque so
                            // it doesn't read as a glitch. Only when the
                            // discount actually applies to this purchase.
                            Label {
                                visible: dlg._free && dlg._eligible
                                Layout.fillWidth: true
                                text: dlg._freeKiho === 1 ? qsTr("Granted free by your School rank.") : qsTr("Granted free by your School rank — %1 remaining.").arg(dlg._freeKiho)
                                font.italic: true
                                font.pixelSize: Theme.fsCaption
                                color: dlg._accent
                                wrapMode: Text.WordWrap
                            }

                            // Path gate line -- who may learn kiho at all.
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Label {
                                    text: dlg._pathMet ? "✓" : "✕"
                                    font.pixelSize: Theme.fsBody
                                    color: dlg._pathMet ? Theme.positive : Theme.accent
                                    Layout.preferredWidth: 14
                                    horizontalAlignment: Text.AlignHCenter
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: dlg._pathMet ? dlg._pathLabel(dlg._selected) : qsTr("Only Monks, Ninja, and Shugenja may learn kiho")
                                    font.pixelSize: Theme.fsBody
                                    color: Theme.ink
                                    opacity: dlg._pathMet ? 0.9 : 1.0
                                    wrapMode: Text.WordWrap
                                }
                            }

                            // Ring / School-rank gate -- only meaningful
                            // once the path gate is met.
                            RowLayout {
                                Layout.fillWidth: true
                                visible: dlg._pathMet
                                spacing: 8

                                Label {
                                    text: dlg._eligible ? "✓" : "✕"
                                    font.pixelSize: Theme.fsBody
                                    color: dlg._eligible ? Theme.positive : Theme.accent
                                    Layout.preferredWidth: 14
                                    horizontalAlignment: Text.AlignHCenter
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: dlg._eligible ? qsTr("Your discipline runs deep enough for this kiho.") : dlg._reasonFor(dlg._selected)
                                    font.pixelSize: Theme.fsBody
                                    color: Theme.ink
                                    opacity: dlg._eligible ? 0.9 : 1.0
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }
                }
            }
        }   // body RowLayout
    }
}
