import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { DatePipe, NgTemplateOutlet } from '@angular/common';
import { ActivatedRoute, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { Subscription } from 'rxjs';
import { Api, Choice, Listing, Options, Row, errorMessages, label } from './api';

export const pages = [
  ['', 'home'], ['jobs', 'jobs'], ['jobs/:id/apply', 'apply'], ['jobs/:id', 'job'],
  ['forum', 'forum'], ['forum/ask', 'ask'], ['forum/:id/edit', 'edit-question'],
  ['forum/:id/answers/:answer/edit', 'edit-answer'], ['forum/:id', 'question'],
  ['login', 'login'], ['register', 'register'], ['dashboard', 'dashboard'],
  ['student/profile', 'student-profile'], ['student/applications', 'student-applications'],
  ['student/saved-jobs', 'saved-jobs'],
  ['company/profile', 'company-profile'], ['company/jobs', 'company-jobs'],
  ['company/jobs/new', 'new-job'], ['company/jobs/:id/edit', 'edit-job'],
  ['company/jobs/:id/applicants', 'applicants'], ['company/applications/:id', 'review'],
];

@Component({selector: 'app-root', imports: [RouterOutlet, RouterLink, RouterLinkActive], template: `
  <a class="skip" href="#main">Skip to content</a>
  <header class="top"><div class="wrap navbar">
    <a class="brand" routerLink="/" aria-label="CareerBridge home">CareerBridge<svg class="brand-accent" width="12" height="9" viewBox="0 0 12 9" aria-hidden="true"><path d="m2 7 4-5 4 5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></a>
    <nav aria-label="Main navigation">
      <a routerLink="/" routerLinkActive="current" [routerLinkActiveOptions]="{exact: true}" ariaCurrentWhenActive="page">Home</a>
      <a routerLink="/jobs" routerLinkActive="current">Find jobs</a>
      <a routerLink="/forum" routerLinkActive="current">Career Q&amp;A</a>
      @if (api.user()) { <a routerLink="/dashboard" routerLinkActive="current">Dashboard</a> }
    </nav>
    <div class="account">@if (api.user(); as user) {
      <img class="account-avatar" width="38" height="38" [src]="api.avatarSrc()" [alt]="user.username + ' profile picture'" (error)="api.useDefaultAvatar()">
      <button type="button" class="button small secondary" [disabled]="busy()" (click)="signOut()">Sign out</button>
    } @else { <a routerLink="/register">Create account</a><a class="button small" routerLink="/login">Sign in</a> }</div>
  </div></header>
  <main class="wrap main" id="main"><router-outlet /></main>
  @if (issue()) { <p class="wrap error" role="alert">{{issue()}}</p> }
  <footer class="foot"><div class="wrap"><strong>CareerBridge</strong><span>Jobs, internships and career conversations.</span></div></footer>
`})
export class App implements OnInit {
  api = inject(Api);
  router = inject(Router);
  issue = signal('');
  busy = signal(false);
  ngOnInit() { void this.api.session().catch(() => this.issue.set('Could not check your session. Make sure Django is running.')); }
  async signOut() {
    this.issue.set(''); this.busy.set(true);
    try { await this.api.post('auth/logout/'); this.api.user.set(null); await this.router.navigateByUrl('/'); }
    catch (error) { this.issue.set(errorMessages(error)[0]); }
    finally { this.busy.set(false); }
  }
}

type Field = {name: string; title: string; type?: string; required?: boolean; choices?: Choice[]; max?: number};
const f = (name: string, title: string, type = 'text', required = true, max?: number): Field => ({name, title, type, required, max});
const statuses: Record<string, string[]> = {applied: ['under_review','not_selected'], under_review: ['interview_approved','not_selected']};
const headings: Record<string, string> = {
  jobs: 'Find jobs and internships', job: 'Job details', apply: 'Apply for this role', forum: 'Career Q&A',
  'saved-jobs': 'Saved jobs',
  question: 'Career discussion', ask: 'Ask a question', 'edit-question': 'Edit your question', 'edit-answer': 'Edit your answer',
  login: 'Welcome back', register: 'Create your account', dashboard: 'Your dashboard',
  'student-profile': 'Student profile', 'student-applications': 'My applications', 'company-profile': 'Company profile',
  'company-jobs': 'My job listings', 'new-job': 'Create a job listing', 'edit-job': 'Edit job listing',
  applicants: 'Job applicants', review: 'Review application',
};

@Component({selector: 'app-page', templateUrl: './page.html', imports: [RouterLink, DatePipe, NgTemplateOutlet]})
export class Page implements OnInit, OnDestroy {
  api = inject(Api);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private sub?: Subscription;
  private serial = 0;
  kind = '';
  id = '';
  answer = '';
  heading = '';
  query: Record<string, string> = {};
  page = 1;
  listing = signal<Listing | null>(null);
  record = signal<Row>({});
  options = signal<Options | null>(null);
  loading = signal(false);
  busy = signal(false);
  bookmarkBusy = signal(false);
  readErrors = signal<string[]>([]);
  formErrors = signal<string[]>([]);
  notice = signal('');
  otherUniversity = signal(false);
  registerRole = signal('student');
  label = label;

  ngOnInit() {
    this.sub = this.route.paramMap.subscribe(params => {
      this.kind = this.route.snapshot.data['kind'];
      this.id = params.get('id') ?? ''; this.answer = params.get('answer') ?? '';
      this.heading = headings[this.kind] || ''; this.query = {}; this.page = 1;
      this.listing.set(null); this.record.set({}); this.notice.set('');
      document.title = this.heading ? `${this.heading} | CareerBridge` : 'CareerBridge';
      void this.load();
    });
  }
  ngOnDestroy() { this.sub?.unsubscribe(); ++this.serial; }

  async load() {
    const seq = ++this.serial;
    this.readErrors.set([]); this.formErrors.set([]);
    if (['home','login','register','ask'].includes(this.kind)) { this.loading.set(false); return; }
    this.loading.set(true);
    const lists: Record<string, string> = {
      jobs: 'jobs/', forum: 'forum/questions/', 'student-applications': 'student/applications/',
      'saved-jobs': 'student/saved-jobs/',
      'company-jobs': 'company/jobs/', applicants: `company/jobs/${this.id}/applicants/`,
    };
    const details: Record<string, string> = {
      job: `jobs/${this.id}/`, apply: `jobs/${this.id}/`, question: `forum/questions/${this.id}/`,
      'edit-question': `forum/questions/${this.id}/`, 'edit-answer': `forum/questions/${this.id}/`,
      'student-profile': 'student/profile/', 'company-profile': 'company/profile/',
      'edit-job': `company/jobs/${this.id}/`, review: `company/applications/${this.id}/`,
    };
    try {
      const [options, listing, record] = await Promise.all([
        ['jobs','student-profile','new-job','edit-job'].includes(this.kind) ? this.api.options() : null,
        lists[this.kind] ? this.api.get<Listing>(lists[this.kind], {...this.query, page: String(this.page)}) : null,
        details[this.kind] ? this.api.get<Row>(details[this.kind]) : null,
        this.kind === 'dashboard' ? this.api.session() : null,
      ]);
      if (seq !== this.serial) return;
      this.options.set(options); this.listing.set(listing);
      let item = record ?? {};
      if (['student-profile','company-profile'].includes(this.kind)) item = item['profile'] ?? {};
      if (this.kind === 'student-profile' && item['university'] && !options?.universities.some(x => x.value === item['university'])) {
        item = {...item, other_university: item['university'], university: '__other__'};
      }
      if (this.kind === 'edit-answer') item = item['answers']?.find((row: Row) => String(row['id']) === this.answer) ?? {};
      if (this.kind === 'review' && item['interview_datetime']) item = {...item,
        interview_datetime: new Date(new Date(item['interview_datetime']).getTime() + 7 * 3600000).toISOString().slice(0,16)};
      this.record.set(item); this.otherUniversity.set(item['university'] === '__other__');
    } catch (error) { if (seq === this.serial) this.readErrors.set(errorMessages(error)); }
    finally { if (seq === this.serial) this.loading.set(false); }
  }

  filter(event: Event) {
    event.preventDefault(); const values = new FormData(event.currentTarget as HTMLFormElement);
    this.query = Object.fromEntries([...values].map(([key,value]) => [key, String(value)]));
    this.page = 1; void this.load();
  }
  reset(form: HTMLFormElement) { form.reset(); this.query = {}; this.page = 1; void this.load(); }
  changePage(change: number) { this.page += change; void this.load(); }

  showBookmark() {
    const user = this.api.user();
    return !user || user.role === 'student';
  }

  async toggleBookmark(job: Row) {
    if (this.bookmarkBusy()) return;
    const user = this.api.user();
    if (!user) { await this.router.navigateByUrl('/login'); return; }
    if (user.role !== 'student') return;
    const target = job['id'];
    const save = !job['bookmarked'];
    const seq = this.serial;
    this.bookmarkBusy.set(true);
    this.formErrors.set([]);
    this.notice.set('');
    try {
      await this.api.post(`jobs/${target}/bookmark/${save ? 'save' : 'remove'}/`);
      if (seq !== this.serial) return;
      if (this.kind === 'saved-jobs' && !save) {
        if (this.page > 1 && this.listing()?.results.length === 1) this.page--;
        await this.load();
      } else {
        this.listing.update(list => list && {...list, results: list.results.map(row =>
          row['id'] === target ? {...row, bookmarked: save} : row)});
        this.record.update(row => row['id'] === target ? {...row, bookmarked: save} : row);
      }
      this.notice.set(save ? 'Job saved to your dashboard.' : 'Job removed from Saved jobs.');
    } catch (error) {
      if (seq === this.serial) this.formErrors.set(errorMessages(error));
    } finally {
      this.bookmarkBusy.set(false);
    }
  }

  fields(): Field[] {
    const opts = this.options();
    const select = (name: string, title: string, choices: Choice[]): Field => ({name, title, choices, type:'select', required:true});
    switch (this.kind) {
      case 'login': return [f('username','Username'), f('password','Password','password')];
      case 'register': return [f('username','Username'), f('email','Email','email'), select('role','Account type', [
        {value:'student',label:'Student'},{value:'company',label:'Company'}]),
        f('password1','Password','password'),f('password2','Confirm password','password'),
        f('profile_picture',this.registerRole() === 'company' ? 'Company logo' : 'Profile photo','image',false)];
      case 'student-profile': return [f('full_name','Full name','text',true,150),
        select('university','University', opts?.universities.filter(x => x.value) ?? []),
        ...(this.otherUniversity() ? [f('other_university','University name','text',true,150)] : []),
        f('degree','Degree','text',true,150),f('phone','Phone','tel',false,30),f('bio','Bio','textarea',false),
        f('cv','CV (PDF, up to 5 MB)','file',false),f('profile_picture','Profile photo','image',false)];
      case 'company-profile': return [f('company_name','Company name','text',true,150),f('industry','Industry','text',true,100),
        f('website','Website','url',false),f('phone','Phone','tel',true,30),f('description','Description','textarea'),f('address','Address','textarea'),
        f('profile_picture','Company logo','image',false)];
      case 'new-job': case 'edit-job': return [f('title','Job title','text',true,150),
        select('job_type','Job type',opts?.job_types ?? []),select('work_mode','Work mode',opts?.work_modes ?? []),
        f('location','Location (required for on-site and hybrid)','text',false,150),f('deadline','Deadline','date'),
        f('description','Description','textarea'),f('requirements','Requirements','textarea')];
      case 'apply': return [f('cover_message','Cover message','textarea',false)];
      case 'review': {
        const current = this.record()['status'];
        return [select('status','Status', (current ? [current,...(statuses[current] ?? [])] : []).map(value => ({value,label:label(value)}))),
          f('interview_datetime','Interview date and time (Bangkok time)','datetime-local',false),
          f('interview_location','Interview location or meeting link','text',false,255),f('company_message','Message to student','textarea',false)];
      }
      case 'ask': case 'edit-question': return [f('title','Title','text',true,200),f('body','Question','textarea')];
      case 'edit-answer': return [f('body','Your answer','textarea')];
      default: return [];
    }
  }

  fieldValue(name: string) { return this.record()[name] ?? (name === 'role' ? this.registerRole() : ''); }
  selectChanged(name: string, value: string) {
    if (name === 'university') this.otherUniversity.set(value === '__other__');
    if (name === 'role') this.registerRole.set(value);
  }
  hasSkill(id: number) { return (this.record()['skills'] ?? []).some((skill: Row) => skill['id'] === id); }
  async submit(event: Event, action = 'main', target?: number) {
    event.preventDefault();
    if (this.busy()) return;
    const element = event.currentTarget instanceof HTMLFormElement ? event.currentTarget : null;
    const form = element ? new FormData(element) : new FormData();
    for (const key of ['cv', 'profile_picture']) {
      const file = form.get(key);
      if (file instanceof File && !file.size && !file.name) form.delete(key);
    }
    const endpoints: Record<string, string> = {
      login:'auth/login/', register:'auth/register/', 'student-profile':'student/profile/save/',
      'company-profile':'company/profile/save/', apply:`jobs/${this.id}/apply/`,
      'new-job':'company/jobs/create/', 'edit-job':`company/jobs/${this.id}/save/`,
      review:`company/applications/${this.id}/review/`, ask:'forum/questions/create/',
      'edit-question':`forum/questions/${this.id}/save/`, 'edit-answer':`forum/answers/${this.answer}/save/`,
    };
    const path = action === 'answer' ? `forum/questions/${this.id}/answer/` : action === 'accept' ?
      `forum/answers/${target}/accept/` : action === 'close' ? `company/jobs/${target}/close/` : endpoints[this.kind];
    if (!path) return;
    this.busy.set(true); this.formErrors.set([]); this.notice.set('');
    try {
      const response = await this.api.post(path, form);
      const picture = form.get('profile_picture');
      if (picture instanceof File && picture.size > 0 && ['student-profile', 'company-profile'].includes(this.kind)) {
        void this.api.refreshAvatar();
      }
      const pictureInput = element?.querySelector<HTMLInputElement>('input[name="profile_picture"]');
      if (pictureInput) pictureInput.value = '';
      let next = '';
      if (['login','register'].includes(this.kind)) {
        await this.api.session();
        next = this.kind === 'register' ? (this.api.user()?.role === 'student' ? '/student/profile' : '/company/profile') : '/dashboard';
      } else if (this.kind === 'apply') next = '/student/applications';
      else if (['new-job','edit-job'].includes(this.kind)) next = '/company/jobs';
      else if (['ask','edit-question','edit-answer'].includes(this.kind)) next = `/forum/${this.kind === 'ask' ? response.id : this.id}`;
      if (next) await this.router.navigateByUrl(next);
      else { await this.load(); this.notice.set(action === 'close' ? 'Listing closed.' : action === 'answer' ? 'Answer posted.' : action === 'accept' ? 'Answer accepted.' : 'Changes saved.'); }
    } catch (error) { this.formErrors.set(errorMessages(error)); }
    finally { this.busy.set(false); }
  }
}
