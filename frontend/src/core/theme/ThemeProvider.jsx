import { useCallback, useMemo, useSyncExternalStore } from "react";

import { ThemeContext } from "./ThemeContextCore";
import { getThemeBridge } from "./themeRuntime";

const themeBridge = getThemeBridge();

export default function ThemeProvider({ children }) {
  const snapshot = useSyncExternalStore(
    themeBridge.subscribe,
    themeBridge.getSnapshot,
    themeBridge.getSnapshot
  );

  const setPreference = useCallback((nextPreference) => {
    themeBridge.setPreference(nextPreference);
  }, []);

  const value = useMemo(
    () => ({
      preference: snapshot.preference,
      resolvedTheme: snapshot.resolvedTheme,
      setPreference,
    }),
    [setPreference, snapshot.preference, snapshot.resolvedTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
