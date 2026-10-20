import { useState } from 'react';
import { Link } from 'expo-router';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { GoogleSignInButton } from '@/auth/google-sign-in';
import { colors } from '@/theme';

export function LandingScreen({ checking, signingIn, googleEnabled, onToken }: {
  checking: boolean;
  signingIn: boolean;
  googleEnabled: boolean;
  onToken: (token: string) => void;
}) {
  const [contentWidth, setContentWidth] = useState(0);
  const wide = contentWidth >= 850;
  return <View style={s.root} onLayout={event => setContentWidth(event.nativeEvent.layout.width)}>
    <View style={[s.hero, wide && s.heroWide]}>
      <View style={s.copy}>
        <View style={s.eyebrow}><View style={s.dot} /><Text style={s.eyebrowText}>MEET YOUR NEXT SET</Text></View>
        <Text accessibilityRole="header" style={[s.title, !wide && s.titleSmall]}>Your workout.{'\n'}A little more{'\n'}<Text style={s.blue}>in your corner.</Text></Text>
        <Text style={s.description}>Choose your muscles. Make the plan yours. Let Mat guide you through each exercise, set, and rest.</Text>
        <View style={s.signIn}>
          {checking ? <View style={s.loading}><ActivityIndicator color={colors.blue} /><Text style={s.note}>Getting things ready…</Text></View> : <GoogleSignInButton disabled={signingIn || !googleEnabled} onToken={onToken} />}
          {signingIn && <View accessibilityLiveRegion="polite" style={s.loading}><ActivityIndicator color={colors.blue} /><Text style={s.note}>Signing you in…</Text></View>}
          <Text style={s.note}>{!checking && !googleEnabled ? 'Sign-in is being set up. Please check back soon.' : 'Sign in to save your name and your workout plan.'}</Text>
          <Link href="https://spotter-sandy-beta.vercel.app/privacy" style={[s.note, { color: colors.blue, textDecorationLine: 'underline' }]}>Privacy policy</Link>
          <Link href="https://spotter-sandy-beta.vercel.app/terms" style={[s.note, { color: colors.blue, textDecorationLine: 'underline' }]}>Terms of service</Link>
        </View>
        <View style={s.promise}><Text style={s.promiseMark}>↗</Text><Text style={s.note}>Built around you. Ready for the next set.</Text></View>
      </View>
      <View style={[s.preview, wide && s.previewWide]}>
        <View style={s.orbitOuter} /><View style={s.orbitInner} />
        <View style={s.sessionCard}>
          <View style={s.cardTop}><Text style={s.cardEyebrow}>YOUR WORKOUT, IN FLOW</Text><Text style={s.live}>●  WITH MAT</Text></View>
          <Text style={s.exercise}>One set at a time.</Text>
          <Text style={s.cardDescription}>A clear plan. A voice in your corner.</Text>
          <View style={s.muscles}><Text style={s.muscle}>CHEST</Text><Text style={s.muscle}>BACK</Text><Text style={s.muscle}>YOUR CHOICE</Text></View>
          <View style={s.progress}><View style={s.progressDone} /></View>
          <View style={s.setRow}><Text style={s.setNumber}>01<Text style={s.setTotal}> / 03</Text></Text><Text style={s.note}>Find your rhythm.</Text></View>
          <View style={s.coach}><View style={s.avatar}><Text style={s.avatarText}>m</Text></View><View style={s.coachCopy}><Text style={s.coachName}>Mat, your voice coach</Text><Text style={s.coachText}>“Take a breath. We’ll go one set at a time.”</Text></View></View>
        </View>
        <View style={s.adaptCard}><View style={s.adaptIcon}><Text style={s.adaptArrow}>⇄</Text></View><View style={s.coachCopy}><Text style={s.coachName}>Equipment taken?</Text><Text style={s.note}>Your plan can move with you.</Text></View></View>
        <Text style={s.previewLabel}>A PREVIEW OF YOUR NEXT WORKOUT</Text>
      </View>
    </View>
    <View style={s.divider} />
    <View style={[s.steps, wide && s.stepsWide]}>
      {[
        ['01', 'Choose your focus.', 'Select the muscles you want to train today.'],
        ['02', 'Make it yours.', 'Review machines, sets, reps, and your chosen weight.'],
        ['03', 'Find your flow.', 'Follow Mat through sets and rests, with controls always close.'],
      ].map(([number, title, description]) => <View key={number} style={s.step}><Text style={s.stepNumber}>{number}</Text><View style={s.stepCopy}><Text style={s.stepTitle}>{title}</Text><Text style={s.note}>{description}</Text></View></View>)}
    </View>
  </View>;
}

const s = StyleSheet.create({
  root: { gap: 36 }, hero: { gap: 40, paddingVertical: 24 }, heroWide: { flexDirection: 'row', alignItems: 'center', paddingVertical: 48 },
  copy: { flex: 1, gap: 26 }, eyebrow: { flexDirection: 'row', gap: 8, alignItems: 'center' }, dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: colors.blue }, eyebrowText: { color: colors.blue, fontWeight: '700', fontSize: 11, letterSpacing: 2 },
  title: { color: colors.ink, fontWeight: '700', fontSize: 66, lineHeight: 70, letterSpacing: -3.5 }, titleSmall: { fontSize: 46, lineHeight: 50, letterSpacing: -2 }, blue: { color: colors.blue },
  description: { fontSize: 18, lineHeight: 29, color: colors.secondary, maxWidth: 450 }, signIn: { gap: 12, alignItems: 'flex-start', minHeight: 78 }, note: { fontSize: 13, lineHeight: 21, color: colors.secondary }, loading: { flexDirection: 'row', gap: 10, alignItems: 'center' }, promise: { flexDirection: 'row', gap: 10, alignItems: 'center' }, promiseMark: { color: colors.blue, fontSize: 20 },
  preview: { minHeight: 430, justifyContent: 'center', paddingHorizontal: 8, paddingTop: 22, paddingBottom: 62 }, previewWide: { width: 470 }, orbitOuter: { position: 'absolute', width: '100%', maxWidth: 360, aspectRatio: 1, borderRadius: 180, backgroundColor: '#E2EAFB', alignSelf: 'center' }, orbitInner: { position: 'absolute', width: '90%', maxWidth: 290, aspectRatio: 1, borderRadius: 145, borderWidth: 1, borderColor: '#CCD9F8', alignSelf: 'center' },
  sessionCard: { backgroundColor: colors.paper, borderRadius: 26, padding: 26, gap: 18, borderWidth: 1, borderColor: '#E0E7F0', boxShadow: '0px 20px 50px rgba(24,43,67,0.09)' }, cardTop: { flexDirection: 'row', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }, cardEyebrow: { color: colors.secondary, fontSize: 9, letterSpacing: 1.5, fontWeight: '700' }, live: { color: colors.good, fontSize: 9, letterSpacing: 1, fontWeight: '700' }, exercise: { color: colors.ink, fontSize: 30, fontWeight: '700', letterSpacing: -1 }, cardDescription: { color: colors.secondary, fontSize: 14, marginTop: -10 },
  muscles: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 }, muscle: { color: colors.blue, backgroundColor: colors.paleBlue, paddingHorizontal: 10, paddingVertical: 7, borderRadius: 7, fontSize: 9, letterSpacing: 1, fontWeight: '700' }, progress: { height: 5, backgroundColor: colors.background, borderRadius: 4, overflow: 'hidden', marginTop: 10 }, progressDone: { width: '33%', height: 5, backgroundColor: colors.blue, borderRadius: 4 }, setRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8 }, setNumber: { color: colors.ink, fontSize: 38, fontWeight: '600', letterSpacing: -1 }, setTotal: { color: '#A5B3C4', fontSize: 24 },
  coach: { flexDirection: 'row', gap: 12, alignItems: 'center', padding: 16, borderRadius: 16, backgroundColor: colors.paleBlue }, avatar: { width: 38, height: 38, borderRadius: 19, backgroundColor: colors.blue, justifyContent: 'center', alignItems: 'center' }, avatarText: { color: '#FFFFFF', fontWeight: '800', fontSize: 25 }, coachCopy: { flex: 1, gap: 3 }, coachName: { fontSize: 13, color: colors.ink, fontWeight: '700' }, coachText: { color: colors.secondary, fontSize: 12, lineHeight: 19 }, adaptCard: { marginTop: -10, marginHorizontal: 24, padding: 16, gap: 12, flexDirection: 'row', alignItems: 'center', backgroundColor: '#F7FAFF', borderRadius: 16, borderWidth: 1, borderColor: colors.border, boxShadow: '0px 8px 24px rgba(24,43,67,0.06)' }, adaptIcon: { backgroundColor: '#E0ECE7', width: 36, height: 36, borderRadius: 12, alignItems: 'center', justifyContent: 'center' }, adaptArrow: { color: colors.good, fontSize: 23 }, previewLabel: { textAlign: 'center', marginTop: 22, fontSize: 9, color: colors.secondary, letterSpacing: 2 },
  divider: { height: 1, backgroundColor: colors.border }, steps: { gap: 24, paddingBottom: 24 }, stepsWide: { flexDirection: 'row', gap: 32 }, step: { flex: 1, flexDirection: 'row', gap: 14 }, stepNumber: { fontSize: 12, color: colors.blue, fontWeight: '700', paddingTop: 3 }, stepCopy: { flex: 1, gap: 6 }, stepTitle: { color: colors.ink, fontSize: 17, fontWeight: '600' },
});
