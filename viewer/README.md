# Viewer provenance

`index.js` and `index.css` are vendored SuperSplat/PlayCanvas viewer assets.
`index.html` is the viewer entry page with this project's PLY/poster bootstrap;
`settings.json` holds the scene presentation settings. The engine was not
authored for this reconstruction project. The exact upstream bundle revision
was not recorded in the published repository and has not been inferred.

Upstream: [SuperSplat Viewer](https://github.com/playcanvas/supersplat-viewer).
The bundled [MIT license](SUPERSPLAT_LICENSE.txt) remains intact. Bundled code is
marked `linguist-vendored` in `.gitattributes`; original Python scripts remain
included in GitHub language statistics.

The default model remains `../model/dragon_object_half_clean.ply`. Serve the
repository root with `python -m http.server 8000` and open
`http://localhost:8000/viewer/`. This audit does not rebuild the third-party
engine or change the deployed scene.
