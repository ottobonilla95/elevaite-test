
export function cls(...classes: (string | false | null | undefined)[]): string {
    return classes.filter(Boolean).join(" ");
}