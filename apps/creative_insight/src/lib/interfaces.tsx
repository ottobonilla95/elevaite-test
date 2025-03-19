// src/types.ts
import { ElementType, ReactNode,HTMLAttributes ,ComponentType, ComponentProps  } from 'react';
import React from 'react';

export interface ResponseData {
  response?: string;
  sql_queries?: string[];
}

export interface AdSurfaceBrandPair {
    Ad_Surface: string;
    Brand: string;
  }
  
export interface CreativeData {
  [key: string]: string | number | boolean | null | undefined;
  Industry_sectors: string;
  AdSurface_Ad_Product: string;
  Brand: string;
  File_type: string;
  Verticals: string;
  MD5hash: string;
  Campaign_Name: string;
  Brand_Logo_Present: string;
  Brand_Logo_Size: string;
  Brand_Logo_Location: string;
  Brand_Logo_When: string;
  Text_Colors_Used: string;
  Text_Sizes: string;
  Text_Locations: string;
  Does_Brand_Name_Appear: string;
  Does_Product_Name_Appear: string;
  Is_Product_Description_In_Text: string;
  No_of_Letters: number;
  No_of_Words: number;
  Colors_Background: string;
  Creative_Video_Length: string;
  Creative_classification: string;
  Text_JSON: string;
  URL: string;
  Unique_ID:string;
  File_Name:string;
  Clickable_Impressions:number;
  Delivered_Trips:number;
  CTR:number;
}
  
export interface CampaignPerformance {
  Campaign_Name: string;
  Start_Date:string;
  End_Date:string;
  Booked_Impressions: number;
  Clickable_Impressions: number;
  Clicks: number;
  Conversion: number;
  Duration: number;
  ECPM:number;
  Budget:number;
  Insights:string;
  Scheduled_Events:string;
}

export interface ApiResponse {
  creative_data: CreativeData[];
  campaigns: string[];
  campaign_data: CampaignPerformance[];
}

export interface PairsResponse {
  adsurface_brand_pairs: AdSurfaceBrandPair[];
}

export interface MarkdownComponentProps extends HTMLAttributes<HTMLElement> {
  node?: Record<string, unknown>;
  children?: ReactNode;
  [key: string]: unknown;
}

export interface CodeProps extends Omit<ComponentProps<'code'>, 'ref'> {
  inline?: boolean;
  className?: string;
  children?: ReactNode;
}


export interface CreateRendererProps {
  className: string;
  Element?: ElementType;
}

export interface MarkdownMessageProps {
  text: string;
}

export interface ElementRefMap {
  h1: HTMLHeadingElement;
  h2: HTMLHeadingElement;
  h3: HTMLHeadingElement;
  p: HTMLParagraphElement;
  strong: HTMLElement;
  em: HTMLElement;
  ul: HTMLUListElement;
  ol: HTMLOListElement;
  li: HTMLLIElement;
  table: HTMLTableElement;
  thead: HTMLTableSectionElement;
  tbody: HTMLTableSectionElement;
  tr: HTMLTableRowElement;
  th: HTMLTableCellElement;
  td: HTMLTableCellElement;
  blockquote: HTMLQuoteElement;
  code: HTMLElement;
  pre: HTMLPreElement;
  span: HTMLSpanElement;
};
