import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import es from "@/locales/es/common.json";
import en from "@/locales/en/common.json";

i18n.use(initReactI18next).init({
  resources: {
    es: { translation: es },
    en: { translation: en },
  },
  lng: "es",
  fallbackLng: "es",
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
