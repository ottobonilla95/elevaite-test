
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/router';
import { useEffect } from 'react';
export default function Home() {

  const{ data:session } = useSession();
  const router = useRouter();
  useEffect(() => {

    if(session){
      //check for token and navigate to homepage
      router.push('/CreativeBriefList');
    } else {
      router.push('/login');
    }
  }, [session, router]);

  


  return (
    <main>
      Redirecting...
    </main>
  )
}
