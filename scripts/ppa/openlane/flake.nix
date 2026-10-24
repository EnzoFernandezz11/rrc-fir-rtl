{
  description = "OpenLane 2 fijado, dependencias para PPA hasta STA post-PnR";
  inputs.openlane.url = "path:/home/enzo/openlane2";
  outputs = { self, openlane }: let
    system = "x86_64-linux";
    pkgs = openlane.legacyPackages.${system};
    lib = pkgs.lib;
    full = pkgs.python3.pkgs.openlane;
    unused = [ pkgs.klayout pkgs.klayout.pymod pkgs.magic-vlsi
               pkgs.netgen pkgs.surelog pkgs.ruby ];
    keep = xs: builtins.filter (p: !(builtins.elem p unused)) xs;
    tools = keep full.includedTools;
    dependencies = keep full.propagatedBuildInputs;
    ppaOpenlane = full.overrideAttrs (old: {
      includedTools = tools;
      propagatedBuildInputs = dependencies;
      computed_PATH = lib.makeBinPath dependencies;
      makeWrapperArgs = [ "--prefix PATH : ${lib.makeBinPath dependencies}" ];
      doCheck = false;
    });
  in {
    devShells.${system}.default = pkgs.mkShell {
      packages = [ ppaOpenlane ] ++ tools;
    };
  };
}
