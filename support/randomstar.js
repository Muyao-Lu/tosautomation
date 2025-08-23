
const main = document.getElementsByTagName("main")[0];

function place_random_star(){
    star = document.createElement("div");
    star.innerHTML = "&#11088;"
    star.className = "star";

    let x = Math.random() * 100;
    let y = Math.random() * 120;

    console.log("pre" + y)
    if (y > 60 && y < 90){
        if (y < 75){
            y -= 20
        }
        else{
            y += 20
        }
    }
    console.log(y);


    const size = Math.random() * 20 + 10
    const cycles = Math.random() * 4 + 2;

    star.style.left = x + "vw";
    star.style.top = y + "vh";
    star.style.fontSize = size + "px";

    star.style.setProperty("--cycles", cycles + "s");

    main.appendChild(star);
}

for (let i=0; i<20; i++){
    place_random_star();
}