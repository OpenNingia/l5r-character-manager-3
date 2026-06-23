// Copyright (C) 2014-2026 Daniele Simonetti
// BuyTattooDialog -- QML-native catalogue picker for receiving a tattoo.
// Replaces the legacy QWidget TattooDialog (l5r/dialogs/kihodlg.py)
// without reusing any of its widgets. Opened from TattooSection:
//     buyTattooDlg.present()
// (The entrypoint is `present` rather than `open` so it does not shadow
// Dialog's built-in open(), which present() calls to pop the modal up.)
//
// A two-pane brushed scroll, kakemono-aspect (taller than wide). The
// left column is the register of not-yet-borne tattoos; the right column
// is the chosen mark's detail -- its source citation and prose. Tattoos
// are free and unconditional (the legacy Togashi-Order gate was disabled
// in practice), so there is no eligibility panel and no XP plaque: the
// footer simply states the mark costs nothing, and the Receive button
// enables as soon as a mark is chosen.
//
// Catalogue entry shape (from appCtrl.availableTattooToBuy()):
//   { id, name, description, source }
// On accept the dialog calls appCtrl.buyTattoo(id).
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
    // The void/mystic hue is the tattoo's identity across the sheet --
    // carried here as the dialog accent so the chooser reads as the same
    // sacred-mark concept as the section. Derived dark tone via
    // Qt.darker (no inline hex).
    readonly property color _accent: Theme.ringVoid
    readonly property color _accentSoft: Qt.lighter(Theme.ringVoid, 1.7)
    readonly property bool _eligible: !!dlg._selected

    // --- size: kakemono proportions, capped to the overlay --------
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 80 : 880, 880)
    height: Math.min(Overlay.overlay ? Overlay.overlay.height - 80 : 640, 640)

    // --- chrome (via L5RDialog) -----------------------------------
    seal: "彫"
    title: qsTr("Receive a Tattoo")
    tagline: qsTr("the Togashi carve their secrets into living flesh")
    accent: _accent
    accentDark: Qt.darker(Theme.ringVoid, 1.3)
    acceptText: qsTr("Receive")
    acceptGlyph: "彫"
    acceptEnabled: dlg._eligible
    statusText: {
        if (!dlg._selected)
            return "";
        return qsTr("This sacred mark costs no experience.");
    }
    onAccepted: {
        if (dlg._selected && appCtrl)
            appCtrl.buyTattoo(dlg._selected.id);
    }

    // --- entrypoint -----------------------------------------------
    function present() {
        dlg._refreshCatalogue();
        dlg._selected = null;
        dlg._search = "";
        dlg.open();
    }

    function _refreshCatalogue() {
        dlg._catalogue = (appCtrl && appCtrl.availableTattooToBuy) ? (appCtrl.availableTattooToBuy() || []) : [];
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
                    placeholder: qsTr("seek a mark by name…")
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
            // LEFT PANE -- the register of marks.
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

                            // Mark sigil -- the void-hued dot that codes
                            // the row as a sacred mark (no element here).
                            Rectangle {
                                Layout.leftMargin: row._active ? 13 : 11
                                Layout.alignment: Qt.AlignVCenter
                                implicitWidth: 8
                                implicitHeight: 8
                                radius: 4
                                color: dlg._accent
                                opacity: 0.9
                            }
                            Label {
                                Layout.fillWidth: true
                                Layout.rightMargin: 12
                                Layout.alignment: Qt.AlignVCenter
                                verticalAlignment: Text.AlignVCenter
                                text: modelData.name || qsTr("(unnamed)")
                                font.pixelSize: Theme.fsBody
                                font.weight: row._active ? Theme.wSemiBold : Theme.wRegular
                                color: Theme.ink
                                elide: Text.ElideRight
                            }
                        }
                    }

                    Label {
                        anchors.centerIn: parent
                        visible: catalogView.count === 0
                        text: dlg._catalogue.length === 0 ? qsTr("every mark is already borne") : qsTr("nothing matches that brushstroke")
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
            // RIGHT PANE -- the chosen mark's detail.
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
                        text: "彫"
                        font.family: Theme.fontKanji
                        font.pixelSize: 130
                        color: dlg._accent
                        opacity: 0.13
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Choose a mark from the register at your left.")
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
                        text: qsTr("Each mark is carved into living flesh and wakes to serve its bearer. They cost no experience to receive.")
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
                        color: dlg._accent
                        opacity: 0.5
                    }

                    // Meta row -- mark chip + source citation.
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        // Mark chip -- filled in the void hue, stamped
                        // with the carved seal.
                        Rectangle {
                            Layout.preferredHeight: 20
                            implicitWidth: markChipLabel.implicitWidth + 18
                            radius: 10
                            color: dlg._accent
                            Label {
                                id: markChipLabel
                                anchors.centerIn: parent
                                text: qsTr("彫  SACRED MARK")
                                font.family: Theme.fontDisplay
                                font.pixelSize: Theme.fsMicro
                                font.weight: Theme.wSemiBold
                                font.letterSpacing: 1.4
                                color: Theme.whiteWash
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

                    // Description -- scrolls if long.
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
                }
            }
        }   // body RowLayout
    }
}
