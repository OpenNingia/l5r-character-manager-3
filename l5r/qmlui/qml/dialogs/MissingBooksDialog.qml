// Copyright (C) 2014-2026 Daniele Simonetti
// MissingBooksDialog -- shown when File > Open is refused because the
// character references datapacks/books that are not installed or active
// (the legacy warn_about_missing_books gate, l5r/ui/advise.py). Replaces
// that QMessageBox with a design-system dialog rather than reusing it.
//
// Opened from MainSheet on appCtrl.loadFailedMissingBooks(books, path):
//     missingBooksDlg.books = books; missingBooksDlg.open();
// The primary action ("Open Library") is wired by the host to jump to the
// Library section; Cancel just dismisses. The working character is never
// touched -- the controller refuses the load before swapping the model.
//
// Data shape (from appCtrl.loadFailedMissingBooks):
//   books: [{ name: "Great Clans", version: "1.6" }, ...]
//
// Crimson accent (§6.16): the load could not proceed, but the dialog is a
// signpost (it points at the fix) rather than an error to dismiss. 蔵
// (kura, storehouse) is the Library section's own seal, tying the dialog
// to where the player resolves it.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Theme 1.0

import "../widgets" as Widgets

Widgets.L5RDialog {
    id: root
    width: Math.min(Overlay.overlay ? Overlay.overlay.width - 120 : 440, 440)
    padding: Theme.s6

    property var books: []

    title: qsTr("Missing datapacks")
    tagline: qsTr("This character cannot be loaded")
    seal: "蔵"
    accent: Theme.accent
    accentDark: Theme.accentMuted
    acceptText: qsTr("Open Library")
    acceptGlyph: "蔵"
    cancelText: qsTr("Cancel")

    ColumnLayout {
        width: parent.width
        spacing: Theme.s3

        Label {
            Layout.fillWidth: true
            text: qsTr("This character references datapacks that are not "
                + "installed or enabled. Install or enable them in the "
                + "Library, then open the character again.")
            wrapMode: Text.WordWrap
            font.family: Theme.fontBody
            font.pixelSize: Theme.fsBody
            color: Theme.ink
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: Theme.borderSubtle
        }

        Repeater {
            model: root.books
            delegate: RowLayout {
                Layout.fillWidth: true
                spacing: Theme.s2

                Label {
                    text: "•"
                    color: Theme.accent
                    font.pixelSize: Theme.fsBody
                }
                Label {
                    Layout.fillWidth: true
                    text: modelData.name
                    font.family: Theme.fontBody
                    font.pixelSize: Theme.fsBody
                    font.weight: Font.DemiBold
                    color: Theme.ink
                    elide: Text.ElideRight
                }
                Label {
                    visible: modelData.version && ("" + modelData.version).length > 0
                    text: qsTr("v%1 or later").arg(modelData.version)
                    font.family: Theme.fontStat
                    font.pixelSize: Theme.fsCaption
                    font.features: Theme.tabularNumbers
                    color: Theme.inkMuted
                }
            }
        }
    }
}
