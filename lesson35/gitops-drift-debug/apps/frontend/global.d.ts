// Global type declarations for React and Material-UI
// This file provides type stubs when node_modules aren't installed locally
// The actual types are available during Docker build

declare module 'react' {
  export interface ReactElement<P = any> {
    type: any;
    props: P;
    key: string | number | null;
  }
  
  export type ReactNode = ReactElement | string | number | boolean | null | undefined | ReactNode[];
  
  export interface ComponentType<P = {}> {
    (props: P): ReactElement | null;
  }
  
  export const StrictMode: ComponentType<{ children?: ReactNode }>;
}

declare module 'react-dom/client' {
  import { ReactNode } from 'react';
  
  export interface Root {
    render(children: ReactNode): void;
    unmount(): void;
  }
  
  export function createRoot(container: Element | DocumentFragment, options?: any): Root;
}

declare module '@mui/material/styles' {
  import { ComponentType, ReactNode } from 'react';
  
  export interface Theme {
    palette: {
      mode: 'light' | 'dark';
      primary: { main: string };
      secondary: { main: string };
    };
  }
  
  export function createTheme(options?: Partial<Theme>): Theme;
  export const ThemeProvider: ComponentType<{ theme: Theme; children?: ReactNode }>;
}

declare module '@mui/material/CssBaseline' {
  import { ComponentType } from 'react';
  const CssBaseline: ComponentType<any>;
  export default CssBaseline;
}

declare module 'react/jsx-runtime' {
  namespace JSX {
    interface Element extends React.ReactElement<any, any> {}
    interface IntrinsicElements {
      [elem: string]: any;
    }
  }
  
  export function jsx(type: any, props: any, key?: any): JSX.Element;
  export function jsxs(type: any, props: any, key?: any): JSX.Element;
  export const Fragment: React.ComponentType<{ children?: React.ReactNode }>;
}
