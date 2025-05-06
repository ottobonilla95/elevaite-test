import "./Discover.scss";



const testData = [
    {
      id: "01",
      title: "Transforming Our Future",
      description: "Exploring the ways AI is shaping the future.",
      image: "discover01.jpg",
    },
    {
      id: "02",
      title: "The Role of AI in Creative Industries",
      description: "Understanding AI's impact on creative fields.",
      image: "discover02.jpg",
    },
    {
      id: "03",
      title: "The Core of AI",
      description: "Diving into the fundamental principles of AI.",
      image: "discover03.jpg",
    },
    {
      id: "04",
      title: "Business Automation",
      description: "How AI is revolutionizing business operations.",
      image: "discover04.jpg",
    },
    {
      id: "05",
      title: "AI in Healthcare",
      description: "Innovations in AI for modern healthcare solutions.",
      image: "discover05.jpg",
    },
    {
      id: "06",
      title: "AI - Future of Work",
      description: "Examining AI's role in the evolving workplace.",
      image: "discover06.jpg",
    },
    {
      id: "07",
      title: "A New Era",
      description: "AI heralding the dawn of a transformative age.",
      image: "discover07.jpg",
    },
    {
      id: "08",
      title: "Creative Industries",
      description: "The intersection of AI and artistic expression.",
      image: "discover08.jpg",
    },
  ];
  






export function Discover(): JSX.Element {
    return (
        <div className="discover-container">
            
            {testData.map(item => 
                <div className="discover-card-container" key={item.id}>
                    <div className="image-container">
                        <img src={`images/${item.image}`} alt={item.image} />
                    </div>
                    <span className="title">{item.title}</span>
                    <span className="description">{item.description}</span>
                </div>
            )}

        </div>
    );
}