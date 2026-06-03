// Copyright (C) 2014-2026 Daniele Simonetti
// Library section (蔵 / "Storehouse"). Datapack management for the QML
// UI: list/enable/disable/delete the installed rule packs, install one
// from a local file, and download the official packs from the canonical
// GitHub repository. When nothing is installed the app is near-useless,
// so the Installed panel foregrounds a "Download the Core datapack" CTA.
//
// Bindings (context property `datapacks` = DatapackProxy):
//   installedPacks  -- [{id, displayName, language, version, authors,
//                        active, isCore}]
//   hasPacks        -- any pack active (drives the MainSheet nudge, not
//                      this section's empty state -- see below)
//   catalogEntries  -- [{name, version, url, size, status,
//                        installedVersion}]; status ∈ available/update/installed
//   catalogState    -- idle | loading | ready | offline | ratelimited | error
//   busy            -- a network op is in flight
// Slots: installFromFileDialog(), setPackActive(id, active), deletePack(id),
//   refreshCatalog(), downloadAndInstall(name, url), downloadCore().
// Feedback toasts ride datapacks.operationFinished, surfaced by MainSheet.
//
// All colours/fonts/spacing come from Theme; null-guard every datapacks.*
// read (the preview tool binds the proxy to null, and the first QML pass
// runs before context properties settle).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../widgets" as Widgets
import Theme 1.0

ColumnLayout {
    id: root
    spacing: Theme.s4

    // Live snapshots, null-guarded.
    readonly property var installed: datapacks ? datapacks.installedPacks : []
    readonly property var catalog: datapacks ? datapacks.catalogEntries : []
    readonly property bool busy: datapacks ? datapacks.busy : false
    readonly property string catalogState: datapacks ? datapacks.catalogState : "idle"
    // The CTA keys off "nothing on disk", NOT hasPacks: a user who
    // disabled every pack must still see them listed below to re-enable.
    readonly property bool nothingInstalled: root.installed.length === 0

    function statusLabel(s) {
        if (s === "installed")
            return qsTr("Installed");
        if (s === "update")
            return qsTr("Update");
        return qsTr("Install");
    }

    function fmtSize(bytes) {
        if (!bytes || bytes <= 0)
            return "";
        if (bytes >= 1048576)
            return (bytes / 1048576).toFixed(1) + " MB";
        if (bytes >= 1024)
            return Math.round(bytes / 1024) + " KB";
        return bytes + " B";
    }

    // ----------------------------------------------------------------
    //  Installed datapacks
    // ----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Installed Datapacks")

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            // --- empty state: foreground the Core download -----------
            ColumnLayout {
                Layout.fillWidth: true
                visible: root.nothingInstalled
                spacing: Theme.s3

                Label {
                    Layout.fillWidth: true
                    text: qsTr("No datapacks yet")
                    font.family: Theme.fontDisplay
                    font.pixelSize: Theme.fsHeading2
                    font.weight: Theme.wSemiBold
                    color: Theme.heading
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Without a datapack the app can't do much. Start with "
                        + "the Core datapack — it carries the base rules, clans, "
                        + "schools and skills.")
                    font.family: Theme.fontBody
                    font.pixelSize: Theme.fsBody
                    color: Theme.ink
                    wrapMode: Text.WordWrap
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.s3
                    Widgets.L5RButton {
                        text: qsTr("Download the Core datapack")
                        glyph: "蔵"
                        enabled: !root.busy
                        onClicked: if (datapacks)
                            datapacks.downloadCore()
                    }
                    Widgets.L5RButton {
                        text: qsTr("Install from file…")
                        primary: false
                        enabled: !root.busy
                        onClicked: if (datapacks)
                            datapacks.installFromFileDialog()
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                }
            }

            // --- installed list --------------------------------------
            Repeater {
                model: root.installed
                delegate: ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Theme.s2

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Theme.s3

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Label {
                                Layout.fillWidth: true
                                text: modelData.displayName
                                font.family: Theme.fontDisplay
                                font.pixelSize: Theme.fsLabel
                                font.weight: Theme.wSemiBold
                                color: Theme.ink
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: {
                                    var bits = [];
                                    if (modelData.version)
                                        bits.push(qsTr("v%1").arg(modelData.version));
                                    bits.push(modelData.language
                                        ? modelData.language : qsTr("All languages"));
                                    if (modelData.authors)
                                        bits.push(modelData.authors);
                                    return bits.join("  •  ");
                                }
                                font.family: Theme.fontBody
                                font.pixelSize: Theme.fsCaption
                                color: Theme.inkMuted
                                elide: Text.ElideRight
                            }
                        }

                        // Enable / disable. Turning Core OFF is destructive
                        // (the app goes dark), so it confirms first and the
                        // switch snaps back until the user accepts.
                        Widgets.L5RToggle {
                            checked: modelData.active
                            onToggled: {
                                if (modelData.isCore && !checked) {
                                    checked = true;
                                    disableCoreDlg.open();
                                } else if (datapacks) {
                                    datapacks.setPackActive(modelData.id, checked);
                                }
                            }
                        }

                        Widgets.L5RButton {
                            text: qsTr("Delete")
                            primary: false
                            enabled: !root.busy
                            onClicked: {
                                deleteDlg.pendingId = modelData.id;
                                deleteDlg.pendingName = modelData.displayName;
                                deleteDlg.pendingIsCore = modelData.isCore;
                                deleteDlg.open();
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: Theme.borderSubtle
                        opacity: 0.5
                        visible: index < root.installed.length - 1
                    }
                }
            }
        }
    }

    // ----------------------------------------------------------------
    //  Get datapacks (local file + official repository)
    // ----------------------------------------------------------------
    Widgets.SheetPanel {
        Layout.fillWidth: true
        title: qsTr("Get Datapacks")

        ColumnLayout {
            width: parent.width
            spacing: Theme.s3

            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.s3

                Widgets.L5RButton {
                    text: qsTr("Install from file…")
                    enabled: !root.busy
                    onClicked: if (datapacks)
                        datapacks.installFromFileDialog()
                }
                Widgets.L5RButton {
                    text: qsTr("Refresh list")
                    primary: false
                    enabled: !root.busy
                    onClicked: if (datapacks)
                        datapacks.refreshCatalog()
                }
                Item {
                    Layout.fillWidth: true
                }
                BusyIndicator {
                    running: root.busy
                    visible: root.busy
                    implicitWidth: 28
                    implicitHeight: 28
                }
            }

            // State captions (only one shows at a time).
            Label {
                Layout.fillWidth: true
                visible: root.catalogState === "idle"
                text: qsTr("Refresh to see the datapacks available from the "
                    + "official repository.")
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsCaption
                font.italic: true
                color: Theme.inkMuted
                wrapMode: Text.WordWrap
            }
            Label {
                Layout.fillWidth: true
                visible: root.catalogState === "loading"
                text: qsTr("Loading the datapack list…")
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsCaption
                font.italic: true
                color: Theme.inkMuted
            }
            Label {
                Layout.fillWidth: true
                visible: root.catalogState === "offline"
                text: qsTr("Couldn't reach the datapack repository. Check your "
                    + "connection and try again.")
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsCaption
                color: Theme.negative
                wrapMode: Text.WordWrap
            }
            Label {
                Layout.fillWidth: true
                visible: root.catalogState === "ratelimited"
                text: qsTr("GitHub is rate-limiting requests right now (it allows "
                    + "a limited number per hour). Please try again later.")
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsCaption
                color: Theme.warning
                wrapMode: Text.WordWrap
            }
            Label {
                Layout.fillWidth: true
                visible: root.catalogState === "error"
                text: qsTr("Couldn't load the datapack list. Please try again.")
                font.family: Theme.fontBody
                font.pixelSize: Theme.fsCaption
                color: Theme.negative
                wrapMode: Text.WordWrap
            }

            // Catalogue list.
            ColumnLayout {
                Layout.fillWidth: true
                visible: root.catalogState === "ready"
                spacing: Theme.s2

                Repeater {
                    model: root.catalog
                    delegate: ColumnLayout {
                        Layout.fillWidth: true
                        spacing: Theme.s2

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: Theme.s3

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                Label {
                                    Layout.fillWidth: true
                                    text: modelData.name
                                    font.family: Theme.fontDisplay
                                    font.pixelSize: Theme.fsLabel
                                    font.weight: Theme.wSemiBold
                                    color: Theme.ink
                                    elide: Text.ElideRight
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: {
                                        var bits = [];
                                        if (modelData.version)
                                            bits.push(qsTr("v%1").arg(modelData.version));
                                        var sz = root.fmtSize(modelData.size);
                                        if (sz)
                                            bits.push(sz);
                                        if (modelData.status === "update" && modelData.installedVersion)
                                            bits.push(qsTr("installed v%1").arg(modelData.installedVersion));
                                        return bits.join("  •  ");
                                    }
                                    font.family: Theme.fontBody
                                    font.pixelSize: Theme.fsCaption
                                    color: Theme.inkMuted
                                    elide: Text.ElideRight
                                }
                            }

                            Widgets.L5RButton {
                                text: root.statusLabel(modelData.status)
                                primary: modelData.status !== "installed"
                                enabled: !root.busy && modelData.status !== "installed"
                                onClicked: if (datapacks)
                                    datapacks.downloadAndInstall(modelData.name, modelData.url)
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: Theme.borderSubtle
                            opacity: 0.5
                            visible: index < root.catalog.length - 1
                        }
                    }
                }

                Label {
                    Layout.fillWidth: true
                    visible: root.catalog.length === 0
                    text: qsTr("No datapacks were found in the latest release.")
                    font.family: Theme.fontBody
                    font.pixelSize: Theme.fsCaption
                    font.italic: true
                    color: Theme.inkMuted
                }
            }
        }
    }

    // ----------------------------------------------------------------
    //  Destructive confirmations (§6.16 -- crimson)
    // ----------------------------------------------------------------
    Widgets.L5RDialog {
        id: deleteDlg
        property string pendingId: ""
        property string pendingName: ""
        property bool pendingIsCore: false

        title: qsTr("Delete datapack?")
        tagline: deleteDlg.pendingName
        seal: "捨"
        accent: Theme.accent
        accentDark: Theme.accentMuted
        padding: Theme.s6
        acceptText: qsTr("Delete")
        acceptGlyph: "捨"
        cancelText: qsTr("Keep")
        onAccepted: if (datapacks)
            datapacks.deletePack(deleteDlg.pendingId)

        Label {
            width: 360
            text: deleteDlg.pendingIsCore
                ? qsTr("Core holds the base rules — deleting it leaves the app "
                    + "unusable until you reinstall it. Delete \"%1\" from disk?")
                    .arg(deleteDlg.pendingName)
                : qsTr("This removes \"%1\" and its content from disk. You can "
                    + "reinstall it later. Continue?").arg(deleteDlg.pendingName)
            wrapMode: Text.WordWrap
            font.family: Theme.fontBody
            font.pixelSize: Theme.fsBody
            color: Theme.ink
        }
    }

    Widgets.L5RDialog {
        id: disableCoreDlg
        title: qsTr("Disable the Core datapack?")
        tagline: qsTr("The base rules will be hidden")
        seal: "蔵"
        accent: Theme.accent
        accentDark: Theme.accentMuted
        padding: Theme.s6
        acceptText: qsTr("Disable")
        cancelText: qsTr("Keep enabled")
        onAccepted: if (datapacks)
            datapacks.setPackActive("core", false)

        Label {
            width: 360
            text: qsTr("Disabling Core hides the base rules, clans, schools and "
                + "skills; the app will be unusable until you re-enable it. "
                + "Continue?")
            wrapMode: Text.WordWrap
            font.family: Theme.fontBody
            font.pixelSize: Theme.fsBody
            color: Theme.ink
        }
    }
}
