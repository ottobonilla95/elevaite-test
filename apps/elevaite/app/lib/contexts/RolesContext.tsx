"use client";
import { createContext, useContext } from "react";



// STRUCTURE 

export interface RolesContextStructure {

}


export const RolesContext = createContext<RolesContextStructure>({

});




// PROVIDER

interface RolesContextProviderProps {
    children: React.ReactNode;
}

export function RolesContextProvider(props: RolesContextProviderProps): JSX.Element {
    return(
        <RolesContext.Provider
            value={ {

            } }
        >
            {props.children}
        </RolesContext.Provider>
    )
}


export function useRoles(): RolesContextStructure {
    return useContext(RolesContext);
}

