import { useEffect } from "react"

export const Tu = () => {
  useEffect(() => { 
    console.log('Tu');
  }, []);
  return (<div>Tu</div>)
}

export default Tu;
