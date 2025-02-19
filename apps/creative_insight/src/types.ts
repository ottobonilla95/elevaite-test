// src/types.ts
export interface AdSurfaceBrandPair {
    Ad_Surface: string;
    Brand: string;
  }
  
export interface CreativeData {
  [key: string]: any;
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
  Booked_Impressions: number;
  Clickable_Impressions: number;
  Clicks: number;
  Conversion: number;
  Duration: number;
  ECPM:number;
  Budget:number;
  Insights:string;
}

export interface CampaignData {
  creativeData: CreativeData[];
  campaignPerformance: CampaignPerformance[];
}