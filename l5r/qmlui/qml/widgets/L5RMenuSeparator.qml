// Copyright (C) 2014-2026 Daniele Simonetti
// Design-system separator for L5RMenu. A single parchment-border hairline
// (§8.3 -- never a solid black line) with a little breathing room above and
// below, in place of the Fusion grey rule.
import QtQuick
import QtQuick.Controls
import Theme 1.0

MenuSeparator {
    id: sep
    padding: 0
    topPadding: Theme.s1
    bottomPadding: Theme.s1
    leftPadding: Theme.s3
    rightPadding: Theme.s3

    contentItem: Rectangle {
        implicitHeight: 1
        color: Theme.divider
        opacity: Theme.dividerOpacity
    }
}
