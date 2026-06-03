// Copyright (C) 2014-2026 Daniele Simonetti
// Design-system dialog shell (§4.3 / §6.14 / §6.15). Factors out the
// chrome every modal repeated by hand: the parchment + rice-paper
// background, the kakemono header (48×48 kanji tile + title + tagline),
// and the footer status bar (optional recap text + Cancel + a primary
// action button). The body is supplied as ordinary child content.
//
// Accent is parameterised so each dialog keeps its identity colour:
// crimson for a Burden, blue for a Blessing, gold/etc. elsewhere.
//
//   accent / accentDark -- header tile + title + primary-button fill
//   accentSoft          -- header-bar wash (derived from accent if unset)
//   seal                -- kanji glyph in the header tile (optional)
//   title / tagline     -- header texts (title is inherited from Dialog)
//   acceptText          -- primary button label (e.g. "Inscribe")
//   acceptGlyph         -- optional kanji on the primary button
//   acceptEnabled       -- enable/disable the primary button
//   cancelText          -- secondary button label (default "Cancel")
//   statusText          -- footer left recap (optional)
//   accepted() / rejected() -- standard Dialog signals; put accept logic
//                          in onAccepted (the primary button calls accept()).
//
// Usage:
//   Widgets.L5RDialog {
//       title: qsTr("Accept a Burden"); tagline: qsTr("…"); seal: "業"
//       accent: Theme.accent; accentDark: Theme.accentMuted
//       acceptText: qsTr("Accept"); acceptGlyph: "業"
//       acceptEnabled: hasSelection; statusText: recap
//       onAccepted: appCtrl.doThing()
//       ColumnLayout { /* body */ }
//   }
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

Dialog {
    id: dlg

    // --- API ------------------------------------------------------
    property color accent: Theme.accent
    property color accentDark: Theme.accentMuted
    // Header-bar wash. Default: paper tinted ~22% by the accent (a pale
    // accent-bg, equivalent to the crimson/blue washes in §2.2).
    property color accentSoft: Qt.tint(Theme.parchment, Qt.rgba(accent.r, accent.g, accent.b, 0.22))
    property string seal: ""
    // `title` is inherited from Dialog (rendered in the custom header
    // below; the built-in title bar is replaced).
    property string tagline: ""
    property string acceptText: qsTr("OK")
    property string acceptGlyph: ""
    property bool acceptEnabled: true
    property string cancelText: qsTr("Cancel")
    property string statusText: ""

    // --- base config (overridable) --------------------------------
    parent: Overlay.overlay
    anchors.centerIn: Overlay.overlay
    modal: true
    // Default padding 0 so a flush full-bleed body (e.g. the two-pane
    // perk catalogue) can reach the framed edges; consumers set their own
    // `padding` for roomier forms. NB: an opaque full-bleed body should
    // use padding >= 1 so the gold frame isn't overdrawn on its sides.
    // (Set `padding` here, not the individual leftPadding/etc., or a
    // consumer's `padding` would be ignored.)
    padding: 0
    standardButtons: Dialog.NoButton
    closePolicy: Popup.CloseOnEscape

    // Ink-on-paper. Dialogs live in the Overlay layer and do NOT inherit
    // the main window's palette, so plain Labels would fall back to the
    // OS palette -- white text on a dark system theme, illegible on the
    // parchment (and against the spec, which never puts white on paper).
    // Pin the parchment palette here so all body content renders
    // dark-on-cream; explicit per-Label colours still win.
    palette.windowText: Theme.ink
    palette.text: Theme.ink
    palette.buttonText: Theme.ink
    palette.base: Theme.parchmentBase
    palette.alternateBase: Theme.parchmentInset
    palette.placeholderText: Theme.inkFaint
    palette.mid: Theme.inkFaint

    // --- backplate: parchment + golden frame + fibre overlay ------
    // ONE 1px gold border on every side. The header band, footer band
    // and body are each inset by 1px (header/footer wrappers below;
    // left/right padding above) so this single frame shows continuously
    // instead of being covered on the top/bottom edges by the bands.
    background: Rectangle {
        color: Theme.parchment
        border.color: Theme.heading
        border.width: 1
        radius: 0
        RicePaperOverlay {}
    }

    // --- header: kakemono band (§6.15) ----------------------------
    // Item wrapper whose inner band is inset 1px (top/left/right) so the
    // gold frame shows through on those edges.
    header: Item {
        implicitHeight: 56
        Rectangle {
            anchors.fill: parent
            anchors.topMargin: 1
            anchors.leftMargin: 1
            anchors.rightMargin: 1
            color: dlg.accentSoft

            // bottom rule
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: dlg.accent
                opacity: 0.4
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 12

                // 48×48 kanji tile: accent fill, white-wash glyph, radius 4.
                Rectangle {
                    visible: dlg.seal.length > 0
                    Layout.preferredWidth: 48
                    Layout.preferredHeight: 48
                    Layout.alignment: Qt.AlignVCenter
                    radius: 4
                    color: dlg.accent
                    Label {
                        anchors.centerIn: parent
                        text: dlg.seal
                        font.family: Theme.fontKanji
                        font.pixelSize: 30
                        color: Theme.whiteWash
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Label {
                        Layout.fillWidth: true
                        text: dlg.title
                        font.family: Theme.fontDisplay
                        font.pixelSize: Theme.fsHeading1
                        font.weight: Theme.headingWeight
                        font.letterSpacing: 1.2
                        color: dlg.accent
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: dlg.tagline.length > 0
                        text: dlg.tagline
                        font.family: Theme.fontBody
                        font.italic: true
                        font.pixelSize: Theme.fsCaption
                        color: Theme.inkMuted
                        elide: Text.ElideRight
                    }
                }
            }
        }
    }

    // --- footer: status bar (§6.14) -------------------------------
    // Item wrapper whose inner band is inset 1px (bottom/left/right) so
    // the gold frame shows through on those edges.
    footer: Item {
        implicitHeight: 48
        Rectangle {
            anchors.fill: parent
            anchors.bottomMargin: 1
            anchors.leftMargin: 1
            anchors.rightMargin: 1
            color: Theme.parchmentSidebar
            RicePaperOverlay {}

            // top rule (parchment-border)
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: Theme.borderSubtle
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 8

                Label {
                    Layout.fillWidth: true
                    visible: dlg.statusText.length > 0
                    text: dlg.statusText
                    font.family: Theme.fontBody
                    font.italic: true
                    font.pixelSize: Theme.fsCaption
                    color: Theme.inkMuted
                    wrapMode: Text.WordWrap
                    verticalAlignment: Text.AlignVCenter
                }
                Item {
                    visible: dlg.statusText.length === 0
                    Layout.fillWidth: true
                }
                L5RButton {
                    text: dlg.cancelText
                    primary: false
                    Layout.alignment: Qt.AlignVCenter
                    onClicked: dlg.reject()
                }
                L5RButton {
                    text: dlg.acceptText
                    glyph: dlg.acceptGlyph
                    accent: dlg.accent
                    accentDark: dlg.accentDark
                    enabled: dlg.acceptEnabled
                    Layout.alignment: Qt.AlignVCenter
                    onClicked: dlg.accept()
                }
            }
        }
    }
}
