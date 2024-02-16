




export function getInitials(name: string): string {
    var splitName = name.trim().split(/\s+/);
    // If there are three names, remove the middle one
    if (splitName.length == 3) {
        splitName.splice(1, 1);
    }
    // If there are more than three names, only keep the first two
    else if (splitName.length > 3) {
        splitName = splitName.slice(0, 2);
    }

    var initials = [];
    for (var i = 0; i < splitName.length; i++) {
        initials.push(splitName[i].charAt(0));
    }

    return initials.join("");
}


