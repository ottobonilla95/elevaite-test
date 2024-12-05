"use client";
import { Breadcrumbs, type BreadcrumbItem } from "@repo/ui/components";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";



export function ContractsBreadcrumbs(): JSX.Element {
    const path = usePathname()
    const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([]);



    useEffect(() => {
        setBreadcrumbs(getBreadcrumbs(path));
    }, [path]);



    function getBreadcrumbs(passedPath: string): BreadcrumbItem[] {
        const breadcrumbList: BreadcrumbItem[] = [];
        const pathList = passedPath.split("/").filter(step => step);
        let accumulatedPath = "";

        for (const [index, step] of pathList.entries()) {
            const label = getLabel(index, step);
            if (!label) continue;

            accumulatedPath += `/${step}`;
            const crumb: BreadcrumbItem = {
                label,
                link: accumulatedPath
            };
            breadcrumbList.push(crumb);
        }
        return breadcrumbList;
    }

    function getLabel(index: number, step: string): string {
        switch(index) {
            case 0: return "Project";
            case 1: return "File View";
            case 2: return step === "compare" ? "Comparison" : "";
            default: return "";
        }
    }


    return (
        <Breadcrumbs items={breadcrumbs} />
    );
}