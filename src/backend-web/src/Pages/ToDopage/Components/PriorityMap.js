const priorityMap = {
    "high":{label: "High", color: '#ff6770'},
    "middle":{label: "Middle", color: '#29ab80'},
    "low":{label: "Low", color: '#749bc5'},
    "undefined":{label: "--", color: '#9B59B6', backgroundColor:'#9B59B62'},
}

const priorityList = (()=>{
    return Object.keys(priorityMap).map( key => {
        return {value:key, ...priorityMap[key]}
    });
})()

export {priorityMap, priorityList}