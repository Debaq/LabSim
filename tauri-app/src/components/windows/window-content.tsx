import { AudiometerPlaceholder } from "./audiometer-placeholder";
import { ImpedancePlaceholder } from "./impedance-placeholder";
import { PatientHistory } from "./patient-history";
import { ClinicalLayout } from "@/components/clinical/clinical-layout";
import { FileExplorerPlaceholder } from "./file-explorer-placeholder";
import { TextEditorPlaceholder } from "./text-editor-placeholder";
import { MessagingApp } from "./messaging-app";
import { PerimetryWindow } from "./perimetry-window";
import { OCTWindow } from "./oct-window";
import { SettingsWindow } from "./settings-window";

interface Props {
  component: string;
}

const componentMap: Record<string, React.ComponentType> = {
  audiometer: AudiometerPlaceholder,
  impedance: ImpedancePlaceholder,
  "patient-history": PatientHistory,
  clinical: ClinicalLayout,
  "file-explorer": FileExplorerPlaceholder,
  "text-editor": TextEditorPlaceholder,
  messaging: MessagingApp,
  perimetry: PerimetryWindow,
  oct: OCTWindow,
  settings: SettingsWindow,
};

export function WindowContent({ component }: Props) {
  const Component = componentMap[component];
  if (!Component) {
    return (
      <div className="flex h-full items-center justify-center ls-bg ls-text-muted">
        Módulo no encontrado: {component}
      </div>
    );
  }
  return <Component />;
}
