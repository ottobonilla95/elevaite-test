// app/page.tsx
"use client";
import { useState, useEffect } from "react";
import { AdSurfaceDropdown } from "../components/AdSurfaceDropdown";
import BrandDropdown from "../components/BrandDropdown";
import CampaignDropdown from "../components/CampaignDropdown";
import CreativeTable from "../components/CreativeTable";
import MainNav from "../components/NavBar";
import CampaignTable from "../components/CampaignTable";
import { AdSurfaceBrandPair, CampaignData, CreativeData, CampaignPerformance } from "../types";
import { Button } from '../components/ui/button';
import {Tabs,TabsContent,TabsList,TabsTrigger} from "../components/ui/tabs";
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "../components/ui/resizable";
import { Icons } from '../components/ui/icons';
import ChatComponent from "../components/ChatComponent";


const API_BASE_URL  = process.env.NEXT_PUBLIC_API_BASE_URL||"http://localhost:8000/api";
const CREATIVE_BASE_URL  = process.env.NEXT_PUBLIC_CREATIVE_BASE_URL||"http://localhost:8080/static/images/";

// const API_BASE_URL = "http://localhost:8000/api";

export default function Home() {
  const [pairs, setPairs] = useState<AdSurfaceBrandPair[]>([]);
  const [adSurfaces, setAdSurfaces] = useState<string[]>([]);
  const [brands,setBrands] = useState<string[]>([]);
  const [selectedAdSurface, setSelectedAdSurface] = useState<string>("");
  const [selectedBrand, setSelectedBrand] = useState<string>("");
  const [selectedCampaign, setSelectedCampaign] = useState<string>("");
  const [campaigns, setCampaigns] = useState<string[]>([]);
  const [data, setData] = useState<CampaignData[]>([]);
  const [creativeData, setCreativeData] = useState<CreativeData[]>([]);
  const [campaignPerformance, setCampaignPerformance] = useState<CampaignPerformance[]>([]);
  const [isChatOpen, setIsChatOpen] = useState(false); 

  useEffect(() => {
    const fetchPairs = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/adsurface_brand_pairs`);
        const json = await response.json();
        setPairs(json.adsurface_brand_pairs);
      } catch (error) {
        console.error("Error fetching pairs:", error);
      }
    };

    fetchPairs();
  }, []);

  useEffect(() => {
    if (pairs.length > 0) {
      const uniqueBrands = Array.from(
        new Set(pairs.map((p) => p.Brand))
      );
      setBrands(uniqueBrands);
      // const uniqueAdSurfaces = Array.from(
      //   new Set(pairs.map((p) => p.Ad_Surface))
      // );
      // setAdSurfaces(uniqueAdSurfaces);
    }
  }, [pairs]);

  useEffect(() => {
    const fetchCampaignData = async () => {
      if (selectedAdSurface && selectedBrand) {
        console.log("The Environment APIs are : ",API_BASE_URL,CREATIVE_BASE_URL);
        try {
          const response = await fetch(
            `${API_BASE_URL}/campaign_data?ad_surface=${selectedAdSurface}&brand=${selectedBrand}`
          );
          const json = await response.json();
          console.log("THE JSON IS:",json);
          console.log("The Environment APIs are : ",API_BASE_URL,CREATIVE_BASE_URL);
          console.log("Received Payload:",json.campaign_data, json.creative_data);
          const campaignPerformance = json.campaign_data.map((item: any) => ({
            Campaign_Name: item.Campaign_Name,
            Booked_Impressions: Number(item.Booked_Impressions),
            Clickable_Impressions: Number(item.Clickable_Impressions),
            Clicks: Number(item.Clicks),
            Conversion: Number(item.Conversion),
            Duration: Number(item.Duration),
            Budget: Number(item.Budget),
            ECPM: Number(item.ECPM),
            Start_Date: item.Start_Date,
            End_Date: item.End_Date,
            Insights: item.insights,
            Scheduled_Events: item.Scheduled_Events,
          }));

          const creativeData = json.creative_data.map((item: any) => ({
            ...item,
            Full_File_URL: CREATIVE_BASE_URL ? `${CREATIVE_BASE_URL}${item.Full_File_URL}` : item.Full_File_URL,
            URL: CREATIVE_BASE_URL ? `${CREATIVE_BASE_URL}${item.URL}` : item.URL,
          }));
          setCreativeData(creativeData);
          setCampaignPerformance(campaignPerformance);
          setCampaigns(json.campaigns);

          if (!selectedCampaign) {
            setSelectedCampaign("");  // Reset selected campaign if not set
          }
          } catch (error) {
            console.error("Error fetching campaign data:", error);
          }
        } else {
          setCreativeData([]);
          setCampaignPerformance([]);
          setCampaigns([]);
        }
      };

    fetchCampaignData();
  }, [selectedAdSurface, selectedBrand, selectedCampaign]);

  const filteredAdSurfaces = Array.from(
    new Set(
      pairs
        .filter((item) => item.Brand === selectedBrand)
        .map((item) => item.Ad_Surface)
    )
  // const filteredBrands = Array.from(
  //   new Set(
  //     pairs
  //       .filter((item) => item.Ad_Surface === selectedAdSurface)
  //       .map((item) => item.Brand)
  //   )
  );
  const selectedCreatives = selectedCampaign ? creativeData.filter(item => item.Campaign_Name === selectedCampaign): creativeData;
  const selectedCampaignPerformance = selectedCampaign? campaignPerformance.filter(item => item.Campaign_Name === selectedCampaign): campaignPerformance;
  const handleChatClose = () => {
    setIsChatOpen(false);
  };
  return (
    <div>
      <MainNav/>  
    <main className="flex min-h-screen flex-col items-left mr-10 ml-10 rounded-lg shadow-md" style={{ backgroundColor: 'hsl(var(--main-background))' }}>
      {!isChatOpen && (
      <Button
        variant="default"
        className="fixed bottom-4 right-4 rounded-full shadow-lg gap-2 hover:scale-105 transition-transform"
        onClick={() => setIsChatOpen(true)}
      >
        <Icons.Message />
        
      </Button>
    )}
    <ResizablePanelGroup direction="horizontal" className="min-h-screen">
    <ResizablePanel defaultSize={70} minSize={50} className="pt-6  pr-8 pl-10">
      <div className="z-10 max-w-5xl w-full  justify-between text-sm lg:flex">
        <h1 className="text-3xl ">Campaign & Creative Insights</h1>
      </div>

      {/* Dropdowns */}
      <div className="flex flex-row space-x-4 mt-4 pl-1" >
        <BrandDropdown
          brands={brands}
          selectedBrand={selectedBrand}
          setSelectedBrand={setSelectedBrand}
          setSelectedCampaign={setSelectedCampaign}
          setSelectedAdSurface={setSelectedAdSurface}
        />
        <AdSurfaceDropdown
          filteredAdSurfaces={filteredAdSurfaces}
          selectedAdSurface={selectedAdSurface}
          setSelectedAdSurface={setSelectedAdSurface}
          selectedBrand={selectedBrand}
          setSelectedCampaign={setSelectedCampaign}
        />
        <CampaignDropdown
          campaigns={campaigns}
          selectedCampaign={selectedCampaign}
          setSelectedCampaign={setSelectedCampaign}
          selectedBrand={selectedBrand}
          selectedAdSurface={selectedAdSurface}
        />
        {/* <Button
          variant="outline"
          className="mt-7 text-muted-foreground"
          onClick={() => {setSelectedAdSurface("");setSelectedBrand("");setSelectedCampaign("");}}>
          <X className="h-4 w-4" /> Clear
        </Button> */}
      </div>
      <Tabs defaultValue="Creative Insights" className="mt-5 mb-5">
        <TabsList className="w-full justify-start">
          <TabsTrigger value="Creative Insights" className="text-l ">Creative Insights</TabsTrigger>
          <TabsTrigger value="Campaign Performance" className="text-l">Campaign Performance</TabsTrigger>
        </TabsList>
      <TabsContent value="Creative Insights">
        <div className="mt-8">
          {/* <h2 className="text-2xl  mb-4">Creative Insights</h2> */}
          <CreativeTable creatives={selectedCreatives} />
        </div>
      </TabsContent>
      <TabsContent value="Campaign Performance">
      <div className="mt-8">
        {/* <h2 className="text-2xl  mb-4">Campaign Performance</h2> */}
        <CampaignTable performanceData={selectedCampaignPerformance} />
      </div>
      </TabsContent>
      </Tabs>
      {selectedAdSurface && selectedBrand && (
        <div className="pb-4 w-full flex justify-end">  {/* Added mt-6 for spacing */}
          <Button variant="outline" className="gap-2" onClick={() => window.print()}>
            <Icons.Share/>Export
          </Button>
        </div>
      )}
    </ResizablePanel>
    {isChatOpen && (<ResizableHandle withHandle className="mx-2" />)}
    {isChatOpen && (
            <ResizablePanel 
              defaultSize={30}
              minSize={25}
              maxSize={45}
              collapsible
              collapsedSize={0}
              className="border-l relative overflow:clip pt-1"
            >
              <ChatComponent onClose={handleChatClose} /> {/* Pass handleChatClose to close the chat */}
            </ResizablePanel>
          )}

    </ResizablePanelGroup>
    </main>
    </div>
  );
}
