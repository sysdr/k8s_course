// Global type declarations to resolve module errors when node_modules aren't installed
// This file provides type stubs for development/IDE purposes
// Actual types come from node_modules during Docker build

declare module 'react' {
  export interface ReactElement<P = any> {
    type: any;
    props: P;
    key: string | number | null;
  }
  
  export type ReactNode = ReactElement | string | number | boolean | null | undefined | ReactNode[];
  
  export interface Component<P = {}, S = {}> {
    props: P;
    state: S;
  }
  
  export interface ComponentType<P = {}> {
    (props: P): ReactElement | null;
  }
  
  export const StrictMode: ComponentType<{ children?: ReactNode }>;
  
  export default {
    StrictMode: {} as ComponentType<{ children?: ReactNode }>
  };
}

declare module 'react-dom/client' {
  import { ReactNode } from 'react';
  
  export interface Root {
    render(children: ReactNode): void;
    unmount(): void;
  }
  
  export function createRoot(
    container: Element | DocumentFragment,
    options?: any
  ): Root;
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
  
  export const ThemeProvider: ComponentType<{
    theme: Theme;
    children?: ReactNode;
  }>;
}

declare module '@mui/material/CssBaseline' {
  import { ComponentType } from 'react';
  const CssBaseline: ComponentType<any>;
  export default CssBaseline;
}

declare module 'react/jsx-runtime' {
  import { ReactElement } from 'react';
  export function jsx(type: any, props: any, key?: any): ReactElement;
  export function jsxs(type: any, props: any, key?: any): ReactElement;
  export const Fragment: ComponentType<{ children?: ReactNode }>;
}
