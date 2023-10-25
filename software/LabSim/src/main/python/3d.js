
var createScene = function () {
    // This creates a basic Babylon Scene object (non-mesh)
    var scene = new BABYLON.Scene(engine);

    var sphere = new BABYLON.SceneLoader.ImportMesh("", "https://f002.backblazeb2.com/file/TMEduca/LabSim/", "cocleas_EISTEIN.glb", scene); 
    // This creates and positions a free camera (non-mesh)

    //var camera = new BABYLON.UniversalCamera("camera1", new BABYLON.Vector3(3.5, 2.5, 254), scene);
    var camera = new BABYLON.ArcRotateCamera("Camera", Math.PI/2, Math.PI/2, 150, BABYLON.Vector3.Zero(), scene);


    // This targets the camera to scene origin
    //camera.setPosition(new BABYLON.Vector3(0,0,20))
    //camera.inputs.addMouseWheel();
    camera.checkCollisions = true
    //camera.applyGravity = true
    //camera.ellipsoid = new Vector3(1, 1, 1)

    camera.setTarget(BABYLON.Vector3.Zero());

    // This attaches the camera to the canvas
    camera.attachControl(canvas, false);

        // This creates a light, aiming 0,1,0 - to the sky (non-mesh)
    var light = new BABYLON.HemisphericLight("light1", new BABYLON.Vector3(0, 1, 0), scene);

    // Default intensity is 1. Let's dim the light a small amount
    light.intensity = 0.7;

    // Our built-in 'sphere' shape.
    //var sphere = BABYLON.MeshBuilder.CreateSphere("sphere", {diameter: 2, segments: 32}, scene);

    // Move the sphere upward 1/2 its height
    //sphere.position.y = 1;
scene.registerBeforeRender(function () {
        light.position = camera.position;
    });
    // Our built-in 'ground' shape.
    //var ground = BABYLON.MeshBuilder.CreateGround("ground", {width: 6, height: 6}, scene);
    canvas.addEventListener("keydown", e=>{
        if(e.key === "f")
        console.log(camera.position)
        console.log(camera.globalPosition)

        });
    return scene;
};