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
import { PracticeSessionsWindow } from "./practice-sessions-window";
import { MyStatsWindow } from "./my-stats-window";
import { AgendaWindow } from "./agenda-window";
import { LarissaWindow } from "./larissa-window";
import { CenterWindow } from "./center-window";
import { RetinographyWindow } from "./retinography-window";
import { CornealTopographyWindow } from "./corneal-topography-window";
import { ManagePatientsWindow } from "./manage-patients-window";
import { CoursesWindow } from "./courses-window";
import { SupervisionWindow } from "./supervision-window";
import { ScheimpflugWindow } from "./scheimpflug-window";
import { VNGWindow } from "./vng-window";
import { VHITWindow } from "./vhit-window";

interface Props {
  component: string;
}

const componentMap: Record<string, React.ComponentType> = {
  audiometer: AudiometerPlaceholder,
  impedance: ImpedancePlaceholder,
  "patient-history": PatientHistory,
  clinical: ClinicalLayout,
  "manage-patients": ManagePatientsWindow,
  "courses": CoursesWindow,
  "supervision": SupervisionWindow,
  "scheimpflug": ScheimpflugWindow,
  "vng": VNGWindow,
  "vhit": VHITWindow,
  "file-explorer": FileExplorerPlaceholder,
  "text-editor": TextEditorPlaceholder,
  messaging: MessagingApp,
  perimetry: PerimetryWindow,
  oct: OCTWindow,
  settings: SettingsWindow,
  "practice-sessions": PracticeSessionsWindow,
  "my-stats": MyStatsWindow,
  agenda: AgendaWindow,
  larissa: LarissaWindow,
  center: CenterWindow,
  retinography: RetinographyWindow,
  "corneal-topography": CornealTopographyWindow,
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
