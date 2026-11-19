import { provideHttpClient, withXsrfConfiguration } from '@angular/common/http';
import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter, withInMemoryScrolling } from '@angular/router';
import { App, Page, pages } from './app';

bootstrapApplication(App, {
  providers: [
    provideHttpClient(withXsrfConfiguration({cookieName: 'csrftoken', headerName: 'X-CSRFToken'})),
    provideRouter([...pages.map(([path, kind]) => ({path, component: Page, data: {kind}})),
      {path: '**', redirectTo: ''}], withInMemoryScrolling({scrollPositionRestoration: 'top'})),
  ],
}).catch(console.error);
